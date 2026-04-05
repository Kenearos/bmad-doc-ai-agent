# AGENTS.md — BMAD-Doc-AI Desktop Agent

Guide for AI coding assistants working on this codebase.

## Overview

Lightweight Python desktop agent that watches local folders and uploads new documents to a BMAD-Doc-AI server. Supports CLI and system tray modes.

## Architecture

```
bmad_agent/
├── cli.py             # Entry point (argparse: --tray, --setup)
├── config.py          # Load/save JSON config from ~/.config/bmad-agent/config.json
├── api_client.py      # ApiClient: login, token refresh, file upload via httpx
├── watcher.py         # FolderWatcher: poll-based folder monitoring, upload, move/delete
├── setup_wizard.py    # Interactive setup (server URL, auth, watched folders)
└── tray.py            # System tray icon via pystray (green/red/yellow status)
```

## Config System

Config file: `~/.config/bmad-agent/config.json`

```json
{
  "server_url": "https://docai.pixel-by-design.de",
  "auth_method": "password",      // "password" or "google"
  "email": "user@example.com",
  "password": "",                  // stored for password auth
  "access_token": "",              // JWT from server
  "refresh_token": "",
  "workspace_id": "",
  "workspace_name": "",
  "watch_dirs": ["~/Documents/BMAD-Eingang"],
  "delete_after_upload": false,
  "move_after_upload": true,       // moves to <dir>/verarbeitet/
  "file_extensions": [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".docx"],
  "poll_interval": 2.0
}
```

- `config.py` — `load_config()` merges saved values with `DEFAULT_CONFIG` (adds missing keys)
- `save_config(config)` writes to `CONFIG_FILE`

## Two Modes

### CLI Mode (`bmad-agent`)
- `cli.py` → `config.py` → `api_client.py` → `watcher.py`
- Runs in terminal, shows upload status via `rich` console
- Ideal for NAS, Raspberry Pi, headless servers

### Tray Mode (`bmad-agent --tray`)
- `cli.py` → `tray.py` → `api_client.py` → `watcher.py`
- System tray icon via `pystray` + `Pillow`
- Colors: green (running), red (error), yellow (paused)
- Desktop notifications via `plyer`
- Right-click menu: pause, settings, quit

## API Integration (`api_client.py`)

`ApiClient` class:
- `login()` — password login via `POST /api/auth/login` or Google token validation
- `_refresh()` — automatic token refresh via `POST /api/auth/refresh`
- `upload(file_path)` — `POST /api/documents/upload` with multipart file + `X-Workspace-Id` header
- Uses `httpx.Client` (sync) with 60s timeout
- Tokens persisted back to config after refresh

## Watcher (`watcher.py`)

`FolderWatcher` class:
- Poll-based: checks watched directories every `poll_interval` seconds
- Filters by `file_extensions`
- Tracks seen files in-memory to avoid re-uploads
- After successful upload: moves to `<dir>/verarbeitet/` or deletes (configurable)
- On upload failure: moves to `<dir>/fehler/`
- `setup()` creates directory structure with console output
- `setup_silent()` same but for tray mode (no console)

## Dependencies

- `httpx` — HTTP client (sync)
- `rich` — Terminal formatting
- `pystray` — System tray icon
- `Pillow` — Image creation for tray icon
- `plyer` — Cross-platform desktop notifications

## How to Add Features

1. **New config option**: Add to `DEFAULT_CONFIG` in `config.py` (merged on load)
2. **New API call**: Add method to `ApiClient` in `api_client.py`
3. **New CLI flag**: Add to argparse in `cli.py`
4. **New tray menu item**: Add to menu builder in `tray.py`

## Entry Point

```
[project.scripts]
bmad-agent = "bmad_agent.cli:main"
```

Install: `pip install -e .` then run `bmad-agent`.
