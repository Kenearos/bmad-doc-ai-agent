"""Ordner-Watcher — überwacht mehrere lokale Ordner und lädt neue Dateien hoch."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from rich.console import Console

from bmad_agent.api_client import ApiClient

console = Console()


class FolderWatcher:
    """Überwacht lokale Ordner auf neue Dateien."""

    def __init__(self, config: dict, client: ApiClient) -> None:
        self._config = config
        self._client = client
        self._watch_dirs = [Path(d) for d in config.get("watch_dirs", [])]
        self._extensions = config.get("file_extensions", [".pdf"])
        self._move = config.get("move_after_upload", True)
        self._delete = config.get("delete_after_upload", False)
        self._poll = config.get("poll_interval", 2.0)
        self._seen: set[str] = set()

    def setup(self) -> None:
        """Erstellt die Ordner-Struktur."""
        for watch_dir in self._watch_dirs:
            watch_dir.mkdir(parents=True, exist_ok=True)
            if self._move:
                (watch_dir / "verarbeitet").mkdir(exist_ok=True)
            (watch_dir / "fehler").mkdir(exist_ok=True)

            # Vorhandene Dateien als gesehen markieren
            for f in watch_dir.iterdir():
                if f.is_file():
                    self._seen.add(str(f))

            console.print(f"  [green]→[/] {watch_dir}")

    def scan_once(self) -> int:
        """Scannt alle Ordner und verarbeitet neue Dateien."""
        count = 0
        for watch_dir in self._watch_dirs:
            if not watch_dir.exists():
                continue
            for file_path in sorted(watch_dir.iterdir()):
                if not file_path.is_file():
                    continue
                if file_path.name.startswith("."):
                    continue
                if str(file_path) in self._seen:
                    continue
                if file_path.suffix.lower() not in self._extensions:
                    continue

                self._seen.add(str(file_path))

                if not self._wait_stable(file_path):
                    continue

                count += self._process_file(file_path, watch_dir)
        return count

    def run_loop(self) -> None:
        """Endlos-Loop."""
        try:
            while True:
                self.scan_once()
                time.sleep(self._poll)
        except KeyboardInterrupt:
            console.print("\n[yellow]Agent beendet.[/]")

    def _process_file(self, file_path: Path, watch_dir: Path) -> int:
        """Verarbeitet eine Datei. Gibt 1 bei Erfolg zurück."""
        console.print(f"  [cyan]↑[/] {file_path.name} ", end="")

        result = self._client.upload_document(file_path)

        if result is None:
            console.print("[red]✗ Fehlgeschlagen[/]")
            self._move_to(file_path, watch_dir / "fehler")
            return 0

        doc_id = result.get("id", "?")
        console.print(f"[green]✓[/] {doc_id[:8]}")

        if self._delete:
            file_path.unlink(missing_ok=True)
        elif self._move:
            self._move_to(file_path, watch_dir / "verarbeitet")

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
        target_dir.mkdir(exist_ok=True)
        target = target_dir / file_path.name
        if target.exists():
            target = target_dir / f"{int(time.time())}_{file_path.name}"
        try:
            shutil.move(str(file_path), str(target))
        except OSError:
            pass
