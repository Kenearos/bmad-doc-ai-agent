"""System-Tray App — Icon mit Menü, Notifications, Hintergrund-Watcher."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from bmad_agent.api_client import ApiClient
from bmad_agent.config import load_config, is_configured, CONFIG_FILE
from bmad_agent.watcher import FolderWatcher

# Status
STATUS_CONNECTING = "connecting"
STATUS_RUNNING = "running"
STATUS_ERROR = "error"
STATUS_PAUSED = "paused"


def run_tray(config: dict) -> None:
    """Startet die Tray-App."""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print("Tray-Modus braucht: pip install pystray Pillow")
        print("Oder starte ohne --tray für CLI-Modus.")
        return

    state = {
        "status": STATUS_CONNECTING,
        "uploaded": 0,
        "errors": 0,
        "paused": False,
        "watcher": None,
        "client": None,
        "stop": False,
    }

    def create_icon(color: str = "green") -> Image.Image:
        """Erstellt ein farbiges Icon."""
        colors = {
            "green": "#10b981",
            "yellow": "#f59e0b",
            "red": "#ef4444",
            "gray": "#6b7280",
        }
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        c = colors.get(color, colors["gray"])
        # Dokument-Form
        draw.rounded_rectangle([8, 4, 56, 60], radius=6, fill=c)
        # Weißes "B" für BMAD
        draw.text((20, 12), "B", fill="white")
        return img

    def update_icon() -> None:
        if state["status"] == STATUS_RUNNING:
            icon.icon = create_icon("green")
            icon.title = f"BMAD Agent — {state['uploaded']} hochgeladen"
        elif state["status"] == STATUS_ERROR:
            icon.icon = create_icon("red")
            icon.title = "BMAD Agent — Verbindungsfehler"
        elif state["status"] == STATUS_PAUSED:
            icon.icon = create_icon("yellow")
            icon.title = "BMAD Agent — Pausiert"
        else:
            icon.icon = create_icon("gray")
            icon.title = "BMAD Agent — Verbindet..."

    def notify(title: str, message: str) -> None:
        """Desktop-Notification."""
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="BMAD-Doc-AI",
                timeout=5,
            )
        except Exception:
            pass  # Notification nicht verfügbar (z.B. auf Server)

    def toggle_pause(icon_ref, item) -> None:
        state["paused"] = not state["paused"]
        state["status"] = STATUS_PAUSED if state["paused"] else STATUS_RUNNING
        update_icon()

    def open_config(icon_ref, item) -> None:
        """Config-Datei im Editor öffnen."""
        import subprocess
        import sys
        if sys.platform == "win32":
            subprocess.Popen(["notepad", str(CONFIG_FILE)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(CONFIG_FILE)])
        else:
            subprocess.Popen(["xdg-open", str(CONFIG_FILE)])

    def quit_agent(icon_ref, item) -> None:
        state["stop"] = True
        icon_ref.stop()

    def watcher_loop() -> None:
        """Hintergrund-Thread: Verbinden + Überwachen."""
        client = ApiClient(config)
        state["client"] = client

        if not client.login():
            state["status"] = STATUS_ERROR
            update_icon()
            notify("BMAD Agent", "Verbindung fehlgeschlagen")
            return

        state["status"] = STATUS_RUNNING
        update_icon()

        ws_name = client.workspace_name or "Workspace"
        notify("BMAD Agent", f"Verbunden mit {ws_name}")

        watcher = FolderWatcher(config, client)
        watcher.setup_silent()
        state["watcher"] = watcher

        while not state["stop"]:
            if not state["paused"]:
                count = watcher.scan_once()
                if count > 0:
                    state["uploaded"] += count
                    update_icon()
                    notify(
                        "BMAD Agent",
                        f"{count} Dokument{'e' if count > 1 else ''} hochgeladen",
                    )
            time.sleep(config.get("poll_interval", 2.0))

        client.close()

    # Tray-Menü
    menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: f"{'▶ Fortsetzen' if state['paused'] else '⏸ Pausieren'}",
            toggle_pause,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda item: f"↑ {state['uploaded']} hochgeladen",
            None,
            enabled=False,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("⚙ Einstellungen", open_config),
        pystray.MenuItem("✕ Beenden", quit_agent),
    )

    icon = pystray.Icon(
        "bmad-agent",
        create_icon("gray"),
        "BMAD Agent — Startet...",
        menu,
    )

    # Watcher in Hintergrund-Thread
    thread = threading.Thread(target=watcher_loop, daemon=True)
    thread.start()

    # Tray-Loop (blockiert)
    icon.run()
