from pathlib import Path
from . import mc_152, mc_189

ADAPTERS = {"152": mc_152, "189": mc_189}

def detect_version(root):
    root = Path(root)
    if (root / "pack.txt").exists() or (root / "terrain.png").exists():
        return "152"
    if (root / "assets" / "minecraft").exists():
        return "189"
    items = list(root.iterdir()) if root.exists() else []
    if len(items) == 1 and items[0].is_dir():
        return detect_version(items[0])
    return None

def get_adapter(version):
    return ADAPTERS.get(version)

