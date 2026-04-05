"""CLI — Startet den BMAD Desktop Agent."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel

from bmad_agent.api_client import ApiClient
from bmad_agent.config import AgentConfig
from bmad_agent.watcher import FolderWatcher

console = Console()


def main() -> None:
    """Haupteinstiegspunkt."""
    console.print(Panel.fit(
        "[bold blue]BMAD-Doc-AI Desktop Agent[/]\n"
        "Lokaler Ordner-Watcher → Cloud-Upload",
        border_style="blue",
    ))
    console.print()

    # Config laden
    config = AgentConfig()

    if not config.email or not config.password:
        console.print("[red]Fehler:[/] BMAD_EMAIL und BMAD_PASSWORD müssen gesetzt sein.")
        console.print()
        console.print("[dim]Erstelle eine .env Datei:[/]")
        console.print('  BMAD_SERVER_URL=https://docai.pixel-by-design.de')
        console.print('  BMAD_EMAIL=deine@email.de')
        console.print('  BMAD_PASSWORD=dein-passwort')
        console.print('  BMAD_WATCH_DIR=/pfad/zum/ordner')
        sys.exit(1)

    # Verbinden
    console.print(f"[bold]Server:[/] {config.server_url}")
    console.print(f"[bold]User:[/] {config.email}")
    console.print()

    client = ApiClient(config)
    console.print("Verbinde... ", end="")

    if not client.login():
        console.print("[red]✗ Login fehlgeschlagen[/]")
        console.print("[dim]Prüfe BMAD_EMAIL und BMAD_PASSWORD in .env[/]")
        sys.exit(1)

    console.print(f"[green]✓[/] Workspace: {client.workspace_id}")
    console.print()

    # Watcher starten
    watcher = FolderWatcher(config, client)
    watcher.setup()

    # Einmal-Scan für bestehende Dateien
    console.print("[bold]Initaler Scan...[/]")
    found = watcher.scan_once()
    if found == 0:
        console.print("[dim]Keine neuen Dateien gefunden.[/]")
    console.print()

    # Endlos-Loop
    watcher.run_loop()
    client.close()


if __name__ == "__main__":
    main()
