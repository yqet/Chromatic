from pathlib import Path
import json

VERSION = "189"
DISPLAY_NAME = "Minecraft 1.8.x"
MAPPING_FILE = Path(__file__).with_name("1.6.1-1.8.9.json")

LABELS = {
    "diamond_sword": "Diamond Sword",
    "diamond_helmet": "Diamond Helmet",
    "diamond_chestplate": "Diamond Chestplate",
    "diamond_leggings": "Diamond Leggings",
    "diamond_boots": "Diamond Boots",
    "golden_apple": "Golden Apple",
}

TARGETS = {
    "diamond_sword": ("assets/minecraft/textures/items/diamond_sword.png",),
    "golden_apple": ("assets/minecraft/textures/items/apple_golden.png",),
    "diamond_helmet": ("assets/minecraft/textures/models/armor/diamond_layer_1.png",),
    "diamond_chestplate": ("assets/minecraft/textures/models/armor/diamond_layer_1.png",),
    "diamond_leggings": ("assets/minecraft/textures/models/armor/diamond_layer_2.png",),
    "diamond_boots": ("assets/minecraft/textures/models/armor/diamond_layer_1.png",),
}


def detect(root: Path):
    return VERSION if (root / "assets" / "minecraft").exists() else None


def load_mapping():
    with MAPPING_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

