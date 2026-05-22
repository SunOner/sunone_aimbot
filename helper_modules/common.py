from __future__ import annotations

import os
from pathlib import Path


MODEL_EXTENSIONS = (".pt", ".engine", ".onnx")
DEVICE_OPTIONS = ["cpu", "0", "1", "2", "3", "4", "5"]


def list_models(models_dir: str | Path = "./models", extensions: tuple[str, ...] = MODEL_EXTENSIONS) -> list[str]:
    models_path = Path(models_dir)
    if not models_path.exists():
        return []

    allowed_extensions = {extension.lower() for extension in extensions}
    return sorted(
        item.name
        for item in models_path.iterdir()
        if item.is_file() and item.suffix.lower() in allowed_extensions
    )


def list_pt_models(models_dir: str | Path = "./models") -> list[str]:
    return list_models(models_dir=models_dir, extensions=(".pt",))


def list_last_checkpoints(root_folder: str = r"runs\detect") -> list[str]:
    last_pt_files: list[str] = []
    root_path = Path(root_folder)
    if not root_path.exists():
        return last_pt_files

    for root, _, files in os.walk(root_path):
        for filename in files:
            if filename == "last.pt":
                last_pt_files.append(str(Path(root) / filename))
    return sorted(last_pt_files)


def safe_index(options: list[str], value: str, default: int = 0) -> int:
    try:
        return options.index(value)
    except ValueError:
        return default
