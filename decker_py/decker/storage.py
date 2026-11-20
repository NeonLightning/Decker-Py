from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from .model import Character


def default_save_directory() -> Path:
    return Path.home() / ".local" / "share" / "decker"


def save_game(character: Character, path: Path) -> Path:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(character.to_dict(), stream, indent=2, sort_keys=True)
        temporary = Path(stream.name)
    temporary.replace(path)
    character.filename = str(path)
    return path


def load_game(path: Path) -> Character:
    with path.expanduser().open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    character = Character.from_dict(payload)
    character.filename = str(path)
    return character


def quick_save_path(character: Character) -> Path:
    if character.filename:
        return Path(character.filename)
    safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in character.name.lower())
    return default_save_directory() / f"{safe_name or 'decker'}.json"
