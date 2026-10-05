from __future__ import annotations

from pathlib import Path
import colorsys
import shutil
import tempfile
import zipfile
import subprocess

from PIL import Image
from adapters import detect_version, get_adapter

_PREVIEW_CACHE = {}
_TEXTURE_PATH_CACHE = {}


def Chromatic_pil(im: Image.Image, hue_deg: float, target_sat: float = 1.0, target_val: float = 1.0) -> Image.Image:
    """Troca a cor mantendo o degradÃª relativo, mas respeitando a cor escolhida."""
    im = im.convert("RGBA").copy()
    px = im.load()
    new_h = (hue_deg % 360.0) / 360.0
    target_sat = max(0.0, min(1.0, float(target_sat)))
    target_val = max(0.0, min(1.0, float(target_val)))
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if s < 0.08 and target_sat > 0.08:
                continue
            out_v = v * target_val
            nr, ng, nb = colorsys.hsv_to_rgb(new_h, target_sat, out_v)
            px[x, y] = (round(nr * 255), round(ng * 255), round(nb * 255), a)
    return im


def _extract_rar(source: Path, root: Path) -> None:
    """Extrai RAR usando o tar/bsdtar disponÃ­vel no Windows 10+ e falha claramente."""
    try:
        result = subprocess.run(
            ["tar", "-xf", str(source), "-C", str(root)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Suporte a .rar requer o tar/bsdtar disponÃ­vel no sistema.") from exc
    if result.returncode != 0:
        raise RuntimeError(f"NÃ£o foi possÃ­vel abrir o RAR: {result.stderr.strip() or 'arquivo invÃ¡lido'}")


def find_texture(source, filename: str):
    """Localiza uma textura dentro de pasta, ZIP, RAR ou 7Z para uso na prÃ©via."""
    source = Path(source)
    if source.is_dir():
        matches = list(source.rglob(filename))
        return matches[0] if matches else None
    key = str(source.resolve())
    root = _PREVIEW_CACHE.get(key)
    if root is None:
        root = Path(tempfile.mkdtemp(prefix="mc_preview_"))
        if source.suffix.lower() == ".zip":
            with zipfile.ZipFile(source, "r") as z:
                z.extractall(root)
        elif source.suffix.lower() == ".rar":
            _extract_rar(source, root)
        elif source.suffix.lower() == ".7z":
            try:
                import py7zr
            except ImportError:
                return None
            with py7zr.SevenZipFile(source, "r") as z:
                z.extractall(root)
        else:
            return None
        _PREVIEW_CACHE[key] = root
    cache_key = (str(root), filename.lower())
    if cache_key in _TEXTURE_PATH_CACHE:
        return _TEXTURE_PATH_CACHE[cache_key]
    matches = list(root.rglob(filename))
    result = matches[0] if matches else None
    _TEXTURE_PATH_CACHE[cache_key] = result
    return result

TARGET_NAMES = {
    "diamond_sword": {"diamond_sword.png"},
    "diamond_helmet": {"diamond_helmet.png"},
    "diamond_chestplate": {"diamond_chestplate.png"},
    "diamond_leggings": {"diamond_leggings.png"},
    "diamond_boots": {"diamond_boots.png"},
    "golden_apple": {"golden_apple.png", "apple_golden.png"},
}
ARMOR_LAYERS = {"diamond_layer_1.png", "diamond_layer_2.png"}
LABELS = {
    "diamond_sword": "Diamond Sword",
    "diamond_helmet": "Diamond Helmet",
    "diamond_chestplate": "Diamond Chestplate",
    "diamond_leggings": "Diamond Leggings",
    "diamond_boots": "Diamond Boots",
    "golden_apple": "Golden Apple",
}


def _is_target(path: Path, selected: set[str], version: str | None = None) -> bool:
    name = path.name.lower()
    if version == "152":
        direct = {
            "sworddiamond.png": "diamond_sword",
            "applegold.png": "golden_apple",
        }
        if name in direct:
            return direct[name] in selected
        if name == "diamond_2.png":
            return "diamond_leggings" in selected
        if name == "diamond_1.png":
            return bool(selected & {"diamond_helmet", "diamond_chestplate", "diamond_boots"})
        return False

    direct = {
        "diamond_sword.png": "diamond_sword",
        "diamond_helmet.png": "diamond_helmet",
        "diamond_chestplate.png": "diamond_chestplate",
        "diamond_leggings.png": "diamond_leggings",
        "diamond_boots.png": "diamond_boots",
        "golden_apple.png": "golden_apple",
        "apple_golden.png": "golden_apple",
    }
    if name in direct:
        return direct[name] in selected
    if name == "diamond_layer_2.png":
        return "diamond_leggings" in selected
    if name == "diamond_layer_1.png":
        return bool(selected & {"diamond_helmet", "diamond_chestplate", "diamond_boots"})
    return False


def Chromatic_image(src: str | Path, dst: str | Path, hue_deg: float, target_sat: float = 1.0, target_val: float = 1.0) -> None:
    im = Chromatic_pil(Image.open(src), hue_deg, target_sat, target_val)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "PNG")


def Chromatic_folder(root: str | Path, output: str | Path, hue_deg: float, selected=None, target_sat: float = 1.0, target_val: float = 1.0) -> int:
    root, output = Path(root), Path(output)
    selected = set(selected or TARGET_NAMES)
    version = detect_version(root)
    count = 0
    for src in root.rglob("*"):
        if not src.is_file():
            continue
        rel, dst = src.relative_to(root), output / src.relative_to(root)
        if src.suffix.lower() == ".png" and _is_target(src, selected, version):
            Chromatic_image(src, dst, hue_deg, target_sat, target_val); count += 1
        else:
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
    return count


def Chromatic_zip(src_zip, output_zip, hue_deg, selected=None, target_sat: float = 1.0, target_val: float = 1.0) -> int:
    selected = set(selected or TARGET_NAMES)
    with tempfile.TemporaryDirectory(prefix="mc_Chromatic_") as tmp:
        root, out_dir = Path(tmp) / "pack", Path(tmp) / "out"
        root.mkdir()
        with zipfile.ZipFile(src_zip, "r") as zin:
            zin.extractall(root)
        count = Chromatic_folder(root, out_dir, hue_deg, selected, target_sat, target_val)
        out_path = Path(output_zip); out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for p in out_dir.rglob("*"):
                if p.is_file():
                    zout.write(p, p.relative_to(out_dir).as_posix())
    return count


def Chromatic_rar(src_rar, output_zip, hue_deg, selected=None, target_sat: float = 1.0, target_val: float = 1.0) -> int:
    """LÃª packs RAR legacy e gera o resultado em ZIP compatÃ­vel."""
    with tempfile.TemporaryDirectory(prefix="mc_Chromatic_rar_") as tmp:
        root, out_dir = Path(tmp) / "pack", Path(tmp) / "out"
        root.mkdir()
        _extract_rar(Path(src_rar), root)
        count = Chromatic_folder(root, out_dir, hue_deg, selected, target_sat, target_val)
        out_path = Path(output_zip); out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for p in out_dir.rglob("*"):
                if p.is_file():
                    zout.write(p, p.relative_to(out_dir).as_posix())
    return count


def Chromatic_7z(src_7z, output_7z, hue_deg, selected=None, target_sat: float = 1.0, target_val: float = 1.0) -> int:
    try:
        import py7zr
    except ImportError as exc:
        raise RuntimeError("Suporte a .7z requer o pacote py7zr.") from exc
    with tempfile.TemporaryDirectory(prefix="mc_Chromatic_7z_") as tmp:
        root, out_dir = Path(tmp) / "pack", Path(tmp) / "out"
        root.mkdir()
        with py7zr.SevenZipFile(src_7z, "r") as archive:
            archive.extractall(root)
        count = Chromatic_folder(root, out_dir, hue_deg, selected, target_sat, target_val)
        with py7zr.SevenZipFile(output_7z, "w") as archive:
            archive.writeall(out_dir, "")
    return count


def detect_pack_version(src) -> str | None:
    """Detects legacy 1.5.2 vs 1.8-style packs using the same structure rules as the converter."""
    src = Path(src)
    if src.is_dir():
        return detect_version(src)
    with tempfile.TemporaryDirectory(prefix="mc_detect_") as tmp:
        root = Path(tmp)
        if src.suffix.lower() == ".zip":
            with zipfile.ZipFile(src, "r") as z: z.extractall(root)
        elif src.suffix.lower() == ".rar":
            _extract_rar(src, root)
        elif src.suffix.lower() == ".7z":
            try:
                import py7zr
            except ImportError:
                return None
            with py7zr.SevenZipFile(src, "r") as z: z.extractall(root)
        else:
            return None
        return detect_version(root)


def Chromatic_path(src, dst, hue_deg, selected=None, target_sat: float = 1.0, target_val: float = 1.0) -> int:
    src = Path(src); dst = Path(dst)
    if src.is_dir():
        if dst.suffix.lower() == ".zip":
            with tempfile.TemporaryDirectory(prefix="mc_Chromatic_dir_") as tmp:
                out_dir = Path(tmp) / "out"
                count = Chromatic_folder(src, out_dir, hue_deg, selected, target_sat, target_val)
                dst.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
                    for p in out_dir.rglob("*"):
                        if p.is_file():
                            zout.write(p, p.relative_to(out_dir).as_posix())
                return count
        return Chromatic_folder(src, dst, hue_deg, selected, target_sat, target_val)
    if src.suffix.lower() == ".zip": return Chromatic_zip(src, dst, hue_deg, selected, target_sat, target_val)
    if src.suffix.lower() == ".rar": return Chromatic_rar(src, dst, hue_deg, selected, target_sat, target_val)
    if src.suffix.lower() == ".7z": return Chromatic_7z(src, dst, hue_deg, selected, target_sat, target_val)
    raise ValueError("Entrada precisa ser uma pasta, .zip, .rar ou .7z.")
def fetch_minecraft_skin(username: str):
    """Resolve a Java username to its current public skin and return a local PNG path.
    Returns (skin_path, model) or (None, None) without failing the Chromatic app.
    """
    import base64
    import json
    import urllib.request

    cache_dir = Path(tempfile.gettempdir()) / "mc_Chromatic_skin_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in username if c.isalnum() or c in "_-.") or "player"
    skin_path = cache_dir / f"{safe}.png"
    meta_path = cache_dir / f"{safe}.json"
    if skin_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            return skin_path, meta.get("model", "classic")
        except Exception:
            return skin_path, "classic"
    try:
        req = urllib.request.Request(
            f"https://api.mojang.com/users/profiles/minecraft/{username}",
            headers={"User-Agent": "ChromaticTexturePreview/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            profile = json.loads(r.read().decode("utf-8"))
        uuid = profile.get("id")
        if not uuid:
            return (skin_path if skin_path.exists() else None, None)
        req = urllib.request.Request(
            f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}",
            headers={"User-Agent": "ChromaticTexturePreview/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            session = json.loads(r.read().decode("utf-8"))
        textures = next((p.get("value") for p in session.get("properties", []) if p.get("name") == "textures"), None)
        if not textures:
            return (skin_path if skin_path.exists() else None, None)
        decoded = json.loads(base64.b64decode(textures).decode("utf-8"))
        skin = decoded.get("textures", {}).get("SKIN", {})
        url = skin.get("url")
        model = skin.get("metadata", {}).get("model", "classic")
        if url:
            req = urllib.request.Request(url, headers={"User-Agent": "ChromaticTexturePreview/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = r.read()
            skin_path.write_bytes(data)
            meta_path.write_text(json.dumps({"username": username, "uuid": uuid, "model": model}), encoding="utf-8")
            return skin_path, model
    except Exception:
        pass
    if skin_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            return skin_path, meta.get("model", "classic")
        except Exception:
            return skin_path, "classic"
    return None, None


def cached_minecraft_skin(username: str):
    cache_dir = Path(tempfile.gettempdir()) / "mc_Chromatic_skin_cache"
    safe = "".join(c for c in username if c.isalnum() or c in "_-.") or "player"
    skin_path = cache_dir / f"{safe}.png"
    meta_path = cache_dir / f"{safe}.json"
    if not skin_path.exists():
        return None, None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        return skin_path, meta.get("model", "classic")
    except Exception:
        return skin_path, "classic"

