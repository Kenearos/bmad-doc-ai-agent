"""Interaktiver Setup-Wizard beim ersten Start."""

from __future__ import annotations

import webbrowser
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from bmad_agent.config import save_config, DEFAULT_CONFIG

console = Console()


def run_setup(config: dict | None = None) -> dict:
    """Interaktiver Setup — fragt Server, Login, Ordner ab."""
    if config is None:
        config = dict(DEFAULT_CONFIG)

    console.print(Panel.fit(
        "[bold blue]BMAD-Doc-AI Agent Setup[/]\n"
        "Einrichtung in 3 Schritten",
        border_style="blue",
    ))
    console.print()

    # Schritt 1: Server
    console.print("[bold]Schritt 1/3: Server[/]")
    config["server_url"] = Prompt.ask(
        "  Server-URL",
        default=config.get("server_url") or "https://docai.pixel-by-design.de",
    )
    console.print()

    # Schritt 2: Login
    console.print("[bold]Schritt 2/3: Anmeldung[/]")
    console.print("  [1] Mit Google anmelden")
    console.print("  [2] Mit E-Mail & Passwort anmelden")
    choice = Prompt.ask("  Wähle", choices=["1", "2"], default="1")

    if choice == "1":
        config["auth_method"] = "google"
        tokens = _google_login(config["server_url"])
        if tokens:
            config["access_token"] = tokens["access_token"]
            config["refresh_token"] = tokens["refresh_token"]
            config["email"] = tokens.get("email", "")
            console.print(f"  [green]✓ Angemeldet als {config['email']}[/]")
        else:
            console.print("  [red]✗ Google-Anmeldung fehlgeschlagen[/]")
            return config
    else:
        config["auth_method"] = "password"
        config["email"] = Prompt.ask("  E-Mail")
        config["password"] = Prompt.ask("  Passwort", password=True)

    console.print()

    # Schritt 3: Ordner
    console.print("[bold]Schritt 3/3: Überwachte Ordner[/]")
    console.print("  [dim]Gib Ordnerpfade ein die überwacht werden sollen.[/]")
    console.print("  [dim]Leere Eingabe zum Beenden.[/]")

    default_dir = str(Path.home() / "Documents" / "BMAD-Eingang")
    watch_dirs: list[str] = []

    while True:
        default = default_dir if not watch_dirs else ""
        path = Prompt.ask(
            f"  Ordner {len(watch_dirs) + 1}",
            default=default,
        )
        if not path:
            break
        # ~ expandieren
        expanded = str(Path(path).expanduser())
        watch_dirs.append(expanded)
        console.print(f"    [green]✓[/] {expanded}")

    if not watch_dirs:
        watch_dirs = [default_dir]
        console.print(f"    [green]✓[/] {default_dir} (Standard)")

    config["watch_dirs"] = watch_dirs
    console.print()

    # Optionen
    config["move_after_upload"] = Confirm.ask(
        "  Dateien nach Upload in 'verarbeitet/' verschieben?",
        default=True,
    )
    if not config["move_after_upload"]:
        config["delete_after_upload"] = Confirm.ask(
            "  Dateien nach Upload löschen?",
            default=False,
        )

    # Speichern
    save_config(config)
    console.print()
    console.print("[bold green]✓ Einrichtung abgeschlossen![/]")
    console.print(f"  [dim]Config gespeichert: ~/.config/bmad-agent/config.json[/]")
    console.print()

    return config


def _google_login(server_url: str) -> dict | None:
    """Google OAuth Flow — öffnet Browser, wartet auf Callback."""
    import httpx

    base = server_url.rstrip("/")
    google_url = f"{base}/api/auth/google"

    console.print()
    console.print("  [bold]Browser öffnet sich für Google-Anmeldung...[/]")
    console.print(f"  [dim]Falls nicht: {google_url}[/]")
    console.print()

    # Browser öffnen
    webbrowser.open(google_url)

    console.print("  [yellow]Melde dich im Browser an und komme dann hierher zurück.[/]")
    console.print("  [dim]Nach der Anmeldung wirst du auf die App weitergeleitet.[/]")
    console.print("  [dim]Kopiere den Token aus der Browser-URL (nach #access_token=...)[/]")
    console.print()

    # Token manuell eingeben (der Callback geht an die Web-App)
    access_token = Prompt.ask("  Access-Token aus Browser einfügen")
    if not access_token:
        return None

    # User-Info holen
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{base}/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            user = resp.json()
            return {
                "access_token": access_token,
                "refresh_token": "",
                "email": user.get("email", ""),
            }
    except Exception:
        return None
