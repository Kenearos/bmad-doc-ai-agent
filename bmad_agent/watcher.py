"""Ordner-Watcher — überwacht lokalen Ordner und lädt neue Dateien hoch."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from rich.console import Console

from bmad_agent.api_client import ApiClient
from bmad_agent.config import AgentConfig

console = Console()


class FolderWatcher:
    """Überwacht einen lokalen Ordner auf neue Dateien."""

    def __init__(self, config: AgentConfig, client: ApiClient) -> None:
        self._config = config
        self._client = client
        self._watch_dir = Path(config.watch_dir)
        self._processed_dir = self._watch_dir / "verarbeitet"
        self._error_dir = self._watch_dir / "fehler"
        self._seen: set[str] = set()

    def setup(self) -> None:
        """Erstellt die Ordner-Struktur."""
        self._watch_dir.mkdir(parents=True, exist_ok=True)
        self._processed_dir.mkdir(exist_ok=True)
        self._error_dir.mkdir(exist_ok=True)

        # Bereits vorhandene Dateien als "gesehen" markieren
        for f in self._watch_dir.iterdir():
            if f.is_file():
                self._seen.add(str(f))

        console.print(f"[bold green]Überwache:[/] {self._watch_dir}")
        console.print(f"[dim]Verarbeitet → {self._processed_dir}[/]")
        console.print(f"[dim]Fehler → {self._error_dir}[/]")
        console.print(f"[dim]Dateitypen: {', '.join(self._config.extensions_list)}[/]")
        console.print()

    def scan_once(self) -> int:
        """Scannt einmal und verarbeitet neue Dateien. Gibt Anzahl hoch."""
        count = 0
        for file_path in sorted(self._watch_dir.iterdir()):
            if not file_path.is_file():
                continue
            if file_path.name.startswith("."):
                continue
            if str(file_path) in self._seen:
                continue
            if file_path.suffix.lower() not in self._config.extensions_list:
                continue

            self._seen.add(str(file_path))

            # Warten bis Datei stabil (nicht mehr geschrieben wird)
            if not self._wait_stable(file_path):
                continue

            count += self._process_file(file_path)

        return count

    def run_loop(self) -> None:
        """Endlos-Loop: Scannt und wartet."""
        console.print("[bold]Agent läuft. Ctrl+C zum Beenden.[/]")
        console.print()

        try:
            while True:
                uploaded = self.scan_once()
                if uploaded > 0:
                    console.print()
                time.sleep(self._config.poll_interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Agent beendet.[/]")

    def _process_file(self, file_path: Path) -> int:
        """Verarbeitet eine einzelne Datei. Gibt 1 bei Erfolg, 0 bei Fehler."""
        console.print(f"  [cyan]↑[/] {file_path.name} ", end="")

        result = self._client.upload_document(file_path)

        if result is None:
            console.print("[red]✗ Upload fehlgeschlagen[/]")
            self._move_to(file_path, self._error_dir)
            return 0

        doc_id = result.get("id", "?")
        console.print(f"[green]✓[/] → {doc_id[:8]}...")

        # Nach Upload: verschieben oder löschen
        if self._config.delete_after_upload:
            file_path.unlink(missing_ok=True)
        elif self._config.move_after_upload:
            self._move_to(file_path, self._processed_dir)

        return 1

    @staticmethod
    def _wait_stable(file_path: Path, attempts: int = 3, delay: float = 0.5) -> bool:
        """Wartet bis Dateigröße stabil ist."""
        try:
            prev = file_path.stat().st_size
            for _ in range(attempts):
                time.sleep(delay)
                if not file_path.exists():
                    return False
                curr = file_path.stat().st_size
                if curr == prev and curr > 0:
                    return True
                prev = curr
            return True
        except OSError:
            return False

    @staticmethod
    def _move_to(file_path: Path, target_dir: Path) -> None:
        """Verschiebt Datei in Zielordner."""
        target = target_dir / file_path.name
        if target.exists():
            target = target_dir / f"{int(time.time())}_{file_path.name}"
        try:
            shutil.move(str(file_path), str(target))
        except OSError:
            pass
