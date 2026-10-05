# Chromatic

Chromatic is a Minecraft texture editing and recoloring tool focused on resource packs from Minecraft 1.5.2 and 1.8.x.

## Overview

The project allows users to select supported Minecraft textures, apply color changes, and inspect the result through a 3D preview. Version-specific adapters keep texture paths, item names, armor layouts, and other differences between supported Minecraft versions isolated from the main engine.

## Features

- Automatic Minecraft resource-pack version detection.
- Support for Minecraft 1.5.2.
- Support for Minecraft 1.8.x.
- Resource packs from folders and compressed archives.
- Individual texture selection and recoloring.
- 3D preview of edited armor and items.
- Inspect Edits preview for reviewing the final result.
- Minecraft-specific adapters for version-dependent texture mappings and names.
- Dark and light interface themes.

## Supported Versions

| Minecraft | Support |
| --- | --- |
| 1.5.2 | Supported |
| 1.8.x | Supported |

## Project Structure

```text
Chromatic/
├── adapters/
│   ├── mc_152.py
│   ├── mc_189.py
│   ├── 1.5.2.json
│   └── 1.6.1-1.8.9.json
├── recolor_gui.py
├── recolor_engine.py
├── preview_dialog.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Architecture

The main engine handles texture processing and recoloring, while the version adapters provide the mappings required for each Minecraft version. The GUI is responsible for interaction and editing controls, and the preview dialog renders the resulting textures in a Minecraft-style 3D model.

This separation makes it possible to add support for additional Minecraft versions without rewriting the core recoloring system.

## Running from Source

Install the dependencies listed in `requirements.txt` and run:

```bash
python recolor_gui.py
```

## Distribution

Chromatic can also be packaged as a standalone Windows executable so users can run the application without installing Python or the project dependencies manually.

## Authors

Created by **blinkzin** and **Miguel**.

## License

Chromatic is distributed under the MIT License. See `LICENSE` for details.
