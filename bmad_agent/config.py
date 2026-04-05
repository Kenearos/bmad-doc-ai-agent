"""Konfiguration — aus .env oder Umgebungsvariablen."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BMAD_",
    )

    # Server-Verbindung
    server_url: str = "https://docai.pixel-by-design.de"
    email: str = ""
    password: str = ""

    # Ordner-Überwachung
    watch_dir: str = str(Path.home() / "Documents" / "BMAD-Eingang")

    # Verhalten
    poll_interval: float = 2.0  # Sekunden zwischen Checks
    delete_after_upload: bool = False  # Datei nach Upload löschen?
    move_after_upload: bool = True  # In "verarbeitet" Ordner verschieben?
    file_extensions: str = ".pdf,.png,.jpg,.jpeg,.tiff,.tif,.docx"

    @property
    def extensions_list(self) -> list[str]:
        return [e.strip().lower() for e in self.file_extensions.split(",")]
