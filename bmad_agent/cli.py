"""CLI — Startet den BMAD Desktop Agent."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel

from bmad_agent.api_client import ApiClient
from bmad_agent.config import load_config, is_configured, CONFIG_FILE
from bmad_agent.setup_wizard import run_setup
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

    # Config laden oder Setup starten
    config = load_config()

    # --setup Flag oder erste Nutzung
    if "--setup" in sys.argv or "--tray" not in sys.argv and not is_configured(config):
        config = run_setup(config)
        if not is_configured(config):
            console.print("[red]Setup nicht abgeschlossen.[/]")
            sys.exit(1)
    else:
        console.print(f"[dim]Config: {CONFIG_FILE}[/]")
        console.print(f"[dim]Ändern: bmad-agent --setup[/]")
        console.print()

    # Tray-Modus?
    if "--tray" in sys.argv:
        from bmad_agent.tray import run_tray
        run_tray(config)
        return

    # CLI-Modus
    console.print(f"[bold]Server:[/] {config['server_url']}")
    console.print(f"[bold]User:[/] {config['email']}")
    if config.get("workspace_name"):
        console.print(f"[bold]Workspace:[/] {config['workspace_name']}")
    console.print()

    client = ApiClient(config)
    console.print("Verbinde... ", end="")

    if not client.login():
        console.print("[red]✗ Login fehlgeschlagen[/]")
        console.print("[dim]Starte 'bmad-agent --setup' um dich neu anzumelden.[/]")
        sys.exit(1)

    console.print(f"[green]✓[/] Workspace: {client.workspace_name or client.workspace_id}")
    console.print()

    # Ordner einrichten
    console.print("[bold]Überwachte Ordner:[/]")
    watcher = FolderWatcher(config, client)
    watcher.setup()
    console.print()

    # Initialer Scan
    found = watcher.scan_once()
    if found == 0:
        console.print("[dim]Keine neuen Dateien.[/]")
    console.print()

    # Loop
    console.print("[bold]Agent läuft. Ctrl+C zum Beenden.[/]")
    console.print()
    watcher.run_loop()
    client.close()


if __name__ == "__main__":
    main()
