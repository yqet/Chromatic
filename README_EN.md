# Chromatic

**Chromatic** is a lightweight Minecraft texture editing and recoloring tool created by **blinkzin**.

The project is designed to make Resource Pack editing easier by allowing users to select specific elements, change their colors, and inspect the result in a 3D preview before exporting the edited texture.

> **Status:** version 1.0 — focused on Minecraft 1.5.2 and 1.8.x

## ✨ Features

- 🎨 Texture recoloring by item/element
- 🔍 Automatic Resource Pack version detection
- 📦 Support for Resource Packs as folders, `.zip`, `.rar`, and `.7z`
- 🧩 Separate adapters for Minecraft 1.5.2 and 1.8.x
- 🖼️ Preserves texture dimensions and structure
- 🧍 3D preview of edited textures
- 🎮 Preview for armor, swords, and other supported items
- 🌙 Dark and light interface modes
- 🌐 Interface prepared for Portuguese and English

## 🕹️ Supported versions

| Minecraft | Support |
|---|---|
| **1.5.2** | ✅ |
| **1.8.x** | ✅ |

The version is detected automatically from the Resource Pack structure/metadata when available. Users do not need to manually select a version in the application.

## 📦 Input formats

Chromatic can work with:

- Resource Pack folders
- `.zip`
- `.rar`
- `.7z`

The project adapts its asset lookup according to the detected Minecraft version and uses version-specific adapters to isolate differences between releases.

## 🏗️ Project structure

```text
Chromatic/
├── recolor_gui.py          # Main graphical interface
├── recolor_engine.py       # Texture analysis and recoloring engine
├── preview_dialog.py       # 3D preview / Inspect Edits
├── adapters/
│   ├── __init__.py
│   ├── mc_152.py           # Minecraft 1.5.2 adapter
│   ├── mc_189.py           # Minecraft 1.8.x adapter
│   ├── 1.5.2.json          # 1.5.2 mappings
│   └── 1.6.1-1.8.9.json    # 1.8.x family mappings
├── Abrir_Chromatic.bat     # Development launcher
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
```

## 🧠 Architecture

Chromatic separates the application into three main layers:

### GUI

`recolor_gui.py` handles the interface, element selection, color controls, and user interaction.

### Engine

`recolor_engine.py` handles texture processing and recoloring operations.

### Adapters

Minecraft versions differ in asset organization and item naming. The adapters isolate those differences so the main engine does not need to know version-specific details.

```text
Resource Pack
      │
      ▼
Version Detection
      │
      ├── Minecraft 1.5.2 ──► mc_152
      │
      └── Minecraft 1.8.x ──► mc_189
      │
      ▼
   Recolor Engine
      │
      ▼
  Edited Texture
      │
      ▼
   3D Preview
```

## 🛠️ Development

Requirements:

- Windows
- Python 3.x
- Dependencies listed in `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python recolor_gui.py
```

Or on Windows:

```text
Abrir_Chromatic.bat
```

## 👤 Author

**blinkzin**

Chromatic was created and developed by blinkzin.

## 📄 License

The project license will be defined by the author before the final GitHub publication.
