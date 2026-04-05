"""Konfiguration — wird interaktiv erstellt und als JSON gespeichert."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "bmad-agent"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "server_url": "https://docai.pixel-by-design.de",
    "auth_method": "",  # "password" oder "google"
    "email": "",
    "password": "",
    "access_token": "",
    "refresh_token": "",
    "workspace_id": "",
    "workspace_name": "",
    "watch_dirs": [],  # Liste von Ordner-Pfaden
    "delete_after_upload": False,
    "move_after_upload": True,
    "file_extensions": [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".docx"],
    "poll_interval": 2.0,
}


def load_config() -> dict:
    """Lädt Config aus ~/.config/bmad-agent/config.json."""
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
        # Fehlende Keys mit Defaults füllen
        merged = dict(DEFAULT_CONFIG)
        merged.update(saved)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """Speichert Config nach ~/.config/bmad-agent/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def is_configured(config: dict) -> bool:
    """Prüft ob der Agent eingerichtet ist."""
    return bool(config.get("email")) and bool(config.get("watch_dirs"))
