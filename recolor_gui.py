from __future__ import annotations

import colorsys
import sys
import threading
from pathlib import Path

from PyQt5.QtCore import Qt, QMimeData, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QFileDialog, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
)

from recolor_engine import LABELS, TARGET_NAMES, Chromatic_path, fetch_minecraft_skin, detect_pack_version
from preview_dialog import PreviewDialog


BG = "#1e1f22"
PANEL = "#2b2d31"
FIELD = "#202124"
BORDER = "#3a3d42"
TEXT = "#f0f0f0"
MUTED = "#aeb4bf"
BLUE = "#356dcc"


class DropFrame(QFrame):
    pathDropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("dropFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        self.label = QLabel("Drag & Drop the resource pack (.zip, .rar, .7z)\nor folder here")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight:600; color:#f0f0f0;")
        layout.addWidget(self.label)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            p = urls[0].toLocalFile()
            if p:
                self.pathDropped.emit(p)
                event.acceptProposedAction()


class HueBar(QWidget):
    hueChanged = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.setFixedSize(24, 165)
        self.hue = 0.0

    def paintEvent(self, _):
        painter = QPainter(self)
        rect = self.rect().adjusted(4, 4, -4, -4)
        grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        for i in range(13):
            pos = i / 12.0
            h = 1.0 - pos
            r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
            grad.setColorAt(pos, QColor(round(r * 255), round(g * 255), round(b * 255)))
        painter.fillRect(rect, grad)
        y = rect.top() + round((1 - self.hue) * rect.height())
        painter.setPen(QPen(Qt.white, 2))
        painter.drawLine(rect.left() - 2, y, rect.right() + 2, y)
        painter.end()

    def mousePressEvent(self, e):
        self._pick(e.pos().y())

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self._pick(e.pos().y())

    def _pick(self, y):
        r = self.rect().adjusted(4, 4, -4, -4)
        self.hue = max(0.0, min(1.0, 1 - (y - r.top()) / max(1, r.height())))
        self.hueChanged.emit(self.hue * 360.0)
        self.update()


class SVPanel(QWidget):
    colorChanged = pyqtSignal(float, float)

    def __init__(self, hue_bar: HueBar):
        super().__init__()
        self.hue_bar = hue_bar
        self.hue = 0.0
        self.saturation = 1.0
        self.value = 1.0
        self.setMinimumSize(270, 165)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hue_bar.hueChanged.connect(self.setHue)

    def setHue(self, degrees):
        self.hue = (degrees % 360) / 360.0
        self.update()
        self.colorChanged.emit(self.saturation, self.value)

    def paintEvent(self, _):
        painter = QPainter(self)
        rect = self.rect().adjusted(4, 4, -4, -4)
        r, g, b = colorsys.hsv_to_rgb(self.hue, 1, 1)
        base = QColor(round(r * 255), round(g * 255), round(b * 255))
        white = QLinearGradient(rect.left(), 0, rect.right(), 0)
        white.setColorAt(0, Qt.white)
        white.setColorAt(1, base)
        painter.fillRect(rect, white)
        black = QLinearGradient(0, rect.top(), 0, rect.bottom())
        black.setColorAt(0, QColor(0, 0, 0, 0))
        black.setColorAt(1, QColor(0, 0, 0, 255))
        painter.fillRect(rect, black)
        x = rect.left() + round(self.saturation * rect.width())
        y = rect.top() + round((1 - self.value) * rect.height())
        painter.setPen(QPen(Qt.white, 2))
        painter.drawEllipse(QPoint(x, y), 5, 5)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(QPoint(x, y), 7, 7)
        painter.end()

    def mousePressEvent(self, e):
        self._pick(e.pos())

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self._pick(e.pos())

    def _pick(self, p):
        rect = self.rect().adjusted(4, 4, -4, -4)
        self.saturation = max(0, min(1, (p.x() - rect.left()) / max(1, rect.width())))
        self.value = max(0, min(1, 1 - (p.y() - rect.top()) / max(1, rect.height())))
        self.colorChanged.emit(self.saturation, self.value)
        self.update()


class ColorPicker(QWidget):
    changed = pyqtSignal(QColor)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(165)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hue = 0.0
        self.saturation = 1.0
        self.value = 1.0
        self.bar = HueBar()
        self.panel = SVPanel(self.bar)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.panel, 1)
        layout.addWidget(self.bar)
        self.bar.hueChanged.connect(self._hue)
        self.panel.colorChanged.connect(self._sv)

    def _hue(self, degrees):
        self.hue = degrees % 360
        self._emit()

    def _sv(self, s, v):
        self.saturation, self.value = s, v
        self._emit()

    def _emit(self):
        r, g, b = colorsys.hsv_to_rgb(self.hue / 360, self.saturation, self.value)
        self.changed.emit(QColor(round(r * 255), round(g * 255), round(b * 255)))

    def color(self):
        r, g, b = colorsys.hsv_to_rgb(self.hue / 360, self.saturation, self.value)
        return QColor(round(r * 255), round(g * 255), round(b * 255))

    def setColor(self, color):
        h, s, v, _ = color.getHsvF()
        self.hue = (0 if h < 0 else h) * 360
        self.saturation = s
        self.value = v
        self.bar.hue = self.hue / 360
        self.panel.hue = self.hue / 360
        self.panel.saturation = s
        self.panel.value = v
        self.bar.update(); self.panel.update(); self._emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chromatic")
        self.setMinimumSize(610, 860)
        self.resize(610, 860)
        self.source = ""
        self.target_color = QColor("#ff3030")
        self._output_auto = True
        self._dark_mode = True
        self._build()
        threading.Thread(target=fetch_minecraft_skin, args=("blinkzin",), daemon=True).start()
        self._theme()
        self._update_color(self.target_color)

    def _build(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(23, 18, 23, 18)
        root.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("Texture Chromatic")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        top.addWidget(title); top.addStretch()
        self.mode = QPushButton("Appearance: Dark Mode  ›")
        self.mode.setFlat(True)
        self.mode.clicked.connect(self._toggle_theme)
        top.addWidget(self.mode)
        root.addLayout(top)

        self.drop = DropFrame(); self.drop.setFixedHeight(120)
        self.drop.pathDropped.connect(self._set_source)
        root.addWidget(self.drop)

        files = QGroupBox("1. Resource Pack File")
        fg = QGridLayout(files); fg.setContentsMargins(10, 10, 10, 10)
        self.input = QLineEdit(); self.input.setPlaceholderText("Input file path (.zip / .rar / .7z / folder)")
        browse = QPushButton("Browse..."); browse.clicked.connect(self._browse_source)
        fg.addWidget(self.input, 0, 0); fg.addWidget(browse, 0, 1)
        root.addWidget(files)

        colorbox = QGroupBox("2. Target Color")
        colorbox.setMinimumHeight(245)
        cg = QVBoxLayout(colorbox); cg.setContentsMargins(10, 12, 10, 12)
        self.picker = ColorPicker(); self.picker.changed.connect(self._update_color)
        picker_stack = QVBoxLayout()
        picker_stack.setContentsMargins(0, 0, 0, 0)
        picker_stack.addWidget(self.picker)
        row = QHBoxLayout()
        self.swatch = QLabel(); self.swatch.setFixedSize(54, 30)
        self.hex = QLineEdit("#FF3030"); self.hex.setReadOnly(True); self.hex.setFixedWidth(110)
        advanced = QPushButton("Open Advanced Picker")
        advanced.setFixedHeight(38)
        advanced.clicked.connect(self._dialog)
        row.addWidget(self.swatch); row.addWidget(self.hex); row.addStretch(); row.addWidget(advanced)
        picker_stack.addLayout(row)
        cg.addLayout(picker_stack)
        root.addWidget(colorbox)

        items = QGroupBox("3. Items to Chromatic")
        ig = QGridLayout(items); ig.setContentsMargins(12, 8, 12, 10)
        self.checks = {}
        order = ["diamond_sword", "diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots", "golden_apple"]
        for i, key in enumerate(order):
            cb = QCheckBox(LABELS[key]); cb.setChecked(True); self.checks[key] = cb
            ig.addWidget(cb, i // 2, i % 2)
        root.addWidget(items)

        out = QGroupBox("4. Output")
        og = QGridLayout(out); og.setContentsMargins(10, 10, 10, 10)
        self.output = QLineEdit(); self.output.setPlaceholderText("Output folder or .zip/.7z filename")
        ob = QPushButton("Browse..."); ob.clicked.connect(self._browse_output)
        og.addWidget(self.output, 0, 0); og.addWidget(ob, 0, 1)
        root.addWidget(out)

        action = QHBoxLayout()
        self.status = QLabel("Ready to Chromatic.")
        self.status.setStyleSheet("color:#aeb4bf;")
        action.addWidget(self.status); action.addStretch()
        self.preview_btn = QPushButton("Inspect Edits")
        self.preview_btn.setMinimumSize(180, 42); self.preview_btn.clicked.connect(self._preview)
        action.addWidget(self.preview_btn)
        self.run_btn = QPushButton("Chromatic")
        self.run_btn.setMinimumSize(180, 42); self.run_btn.clicked.connect(self._run)
        action.addWidget(self.run_btn)
        root.addLayout(action)

    def _apply_titlebar_theme(self):
        # Keep the native Windows title bar completely static/default.
        return

    def _theme(self):
        if self._dark_mode:
            bg, panel, field, border, text, muted = BG, PANEL, FIELD, BORDER, TEXT, MUTED
            button, hover, drop, indicator = "#343740", "#41454f", "#2a2c30", "#555962"
            self.mode.setText("Appearance: Dark Mode  ›")
        else:
            bg, panel, field, border, text, muted = "#f5f6f8", "#ffffff", "#ffffff", "#d7dbe2", "#20242a", "#66707d"
            button, hover, drop, indicator = "#e9ebef", "#dde1e7", "#ffffff", "#aeb5bf"
            self.mode.setText("Appearance: Light Mode  ›")
        self.setStyleSheet(f"""
            QWidget {{ background:{bg}; color:{text}; font-family:'Segoe UI'; font-size:13px; }}
            QGroupBox {{ background:{panel}; border:1px solid {border}; border-radius:8px; margin-top:9px; padding-top:10px; font-weight:600; }}
            QGroupBox::title {{ subcontrol-origin: margin; left:12px; padding:0 5px; background:{bg}; }}
            QLineEdit {{ background:{field}; border:1px solid {border}; border-radius:6px; padding:9px; color:{text}; selection-background-color:{BLUE}; }}
            QPushButton {{ background:{button}; border:1px solid {border}; border-radius:6px; padding:9px 14px; color:{text}; }}
            QPushButton:hover {{ background:{hover}; }}
            QPushButton#primary {{ background:{BLUE}; color:white; border:0; }}
            QCheckBox {{ spacing:8px; padding:5px; }}
            QCheckBox::indicator {{ width:19px; height:19px; }}
            QCheckBox::indicator:checked {{ background:{BLUE}; border-radius:4px; }}
            QCheckBox::indicator:unchecked {{ background:{field}; border:1px solid {indicator}; border-radius:4px; }}
            QFrame#dropFrame {{ background:{drop}; border:1px solid {border}; border-radius:8px; }}
            QScrollArea {{ background:{bg}; border:0; }}
            QToolTip {{ background:{panel}; color:{text}; border:1px solid {border}; padding:5px; }}
        """)
        self.run_btn.setObjectName("primary")
        self.mode.setStyleSheet(f"background:transparent; border:0; color:{text}; padding:4px 2px;")
        self.drop.label.setStyleSheet(f"font-weight:600; color:{text};")
        self.status.setStyleSheet(f"color:{muted};")

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._theme()

    def _color_label(self):
        known = {
            "ff0000": "VERMELHO", "0000ff": "AZUL", "00ff00": "VERDE",
            "ffff00": "AMARELO", "ff00ff": "ROXO", "00ffff": "CIANO",
            "ffa500": "LARANJA", "ffffff": "BRANCO", "000000": "PRETO",
            "ff3030": "VERMELHO",
        }
        key = self.target_color.name().lstrip("#").lower()
        return known.get(key, key.upper())

    def _set_auto_output(self):
        if not self.source or not self._output_auto:
            return
        path = Path(self.source)
        label = self._color_label()
        if path.is_dir():
            self.output.setText(str(path.parent / f"{path.name}_{label}"))
        elif path.suffix.lower() in (".zip", ".rar", ".7z"):
            suffix = ".zip" if path.suffix.lower() == ".rar" else path.suffix.lower()
            self.output.setText(str(path.with_name(f"{path.stem}_{label}{suffix}")))


    def _set_source(self, p):
        self.source = p; self.input.setText(p)
        self._output_auto = True
        self._set_auto_output()
        version = detect_pack_version(p)
        label = {"152": "Minecraft 1.5.2", "189": "Minecraft 1.8.x"}.get(version, "Unknown version")
        self.status.setText(f"Detected: {label}")

    def _browse_source(self):
        p, _ = QFileDialog.getOpenFileName(self, "Selecionar resource pack", "", "Resource Pack (*.zip *.rar *.7z);;ZIP (*.zip);;RAR (*.rar);;7Z (*.7z)")
        if p: self._set_source(p)
        else:
            p = QFileDialog.getExistingDirectory(self, "Selecionar pasta do resource pack")
            if p: self._set_source(p)

    def _browse_output(self):
        src = Path(self.input.text()) if self.input.text() else None
        if not src or not src.exists():
            p = QFileDialog.getExistingDirectory(self, "Pasta de destino")
        elif src.is_dir():
            p = QFileDialog.getExistingDirectory(self, "Pasta de destino")
        elif src.suffix.lower() in ('.zip', '.7z'):
            suffix = src.suffix.lower()
            p, _ = QFileDialog.getSaveFileName(
                self, "Salvar resource pack",
                str(src.with_name(src.stem + '_' + self._color_label() + suffix)),
                f"*{suffix}")
        elif src.suffix.lower() == '.rar':
            p, _ = QFileDialog.getSaveFileName(
                self, "Salvar resource pack",
                str(src.with_name(src.stem + '_' + self._color_label() + '.zip')),
                "ZIP (*.zip)")
        else:
            p = None
        if p:
            self.output.setText(p)
            self._output_auto = False

    def _dialog(self):
        c = QColorDialog.getColor(self.target_color, self, "Escolher cor")
        if c.isValid(): self.picker.setColor(c)

    def _update_color(self, color):
        self.target_color = color
        self.swatch.setStyleSheet(f"background:{color.name().upper()}; border:1px solid #666; border-radius:4px;")
        self.hex.setText(color.name().upper())
        self._set_auto_output()

    def _preview(self):
        src = self.input.text().strip()
        if not src or not Path(src).exists():
            QMessageBox.warning(self, "Prévia", "Selecione primeiro um resource pack .zip/.7z ou uma pasta.")
            return
        selected = [k for k, cb in self.checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Prévia", "Selecione pelo menos um item.")
            return
        try:
            hue, sat, val, _ = self.target_color.getHsvF()
            hue = 0.0 if hue < 0 else hue * 360.0
            dlg = PreviewDialog(src, float(hue), float(sat), float(val), selected, self)
            dlg.exec_()
        except Exception as exc:
            QMessageBox.critical(self, "Prévia", f"Não foi possível gerar a prévia.\n\n{exc}")

    def _run(self):
        src = self.input.text().strip(); dst = self.output.text().strip()
        if not src or not Path(src).exists():
            QMessageBox.warning(self, "Entrada", "Selecione um resource pack .zip/.7z ou uma pasta.")
            return
        if not dst:
            QMessageBox.warning(self, "Saída", "Escolha o destino da textura Chromaticida.")
            return
        selected = [k for k, cb in self.checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Itens", "Selecione pelo menos um item.")
            return
        try:
            self.run_btn.setEnabled(False); self.status.setText("Chromaticindo..."); QApplication.processEvents()
            hue, sat, val, _ = self.target_color.getHsvF()
            hue = 0.0 if hue < 0 else hue * 360.0
            count = Chromatic_path(src, dst, float(hue), selected, float(sat), float(val))
            self.status.setText(f"Concluído — {count} textura(s) alterada(s).")
            QMessageBox.information(self, "Concluído", f"Chromatic Concluído.\n\n{count} textura(s) alterada(s).\nO degradê, sombras e transparência foram preservados.")
        except Exception as exc:
            self.status.setText("Erro durante o Chromatic.")
            QMessageBox.critical(self, "Erro", str(exc))
        finally:
            self.run_btn.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon_path = Path(sys._MEIPASS) / "chromatic.ico" if getattr(sys, "frozen", False) else Path(__file__).resolve().parent / "chromatic.ico"
    app.setWindowIcon(QIcon(str(icon_path)))
    win = MainWindow()
    win.setWindowIcon(QIcon(str(icon_path)))
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()



