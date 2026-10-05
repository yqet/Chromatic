from pathlib import Path
import json

VERSION = "152"
DISPLAY_NAME = "Minecraft 1.5.2"
MAPPING_FILE = Path(__file__).with_name("1.5.2.json")

LABELS = {
    "diamond_sword": "Diamond Sword",
    "diamond_helmet": "Diamond Helmet",
    "diamond_chestplate": "Diamond Chestplate",
    "diamond_leggings": "Diamond Leggings",
    "diamond_boots": "Diamond Boots",
    "golden_apple": "Golden Apple",
}

# Names taken from the 1.5.2 mapping supplied by the texture converter.
TARGETS = {
    "diamond_sword": ("textures/items/swordDiamond.png", "gui/items.png"),
    "golden_apple": ("textures/items/appleGold.png", "gui/items.png"),
    "diamond_helmet": ("armor/diamond_1.png",),
    "diamond_chestplate": ("armor/diamond_1.png",),
    "diamond_leggings": ("armor/diamond_2.png",),
    "diamond_boots": ("armor/diamond_1.png",),
}


def detect(root: Path):
    return VERSION if (root / "pack.txt").exists() or (root / "terrain.png").exists() else None


def load_mapping():
    with MAPPING_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

