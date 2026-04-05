"""API-Client — Authentifizierung und Dokument-Upload."""

from __future__ import annotations

from pathlib import Path

import httpx

from bmad_agent.config import AgentConfig


class ApiClient:
    """Verbindet sich mit dem BMAD-Doc-AI Server."""

    def __init__(self, config: AgentConfig) -> None:
        self._config = config
        self._base_url = config.server_url.rstrip("/")
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._workspace_id: str | None = None
        self._client = httpx.Client(timeout=60.0)

    def login(self) -> bool:
        """Anmelden und Tokens + Workspace-ID holen."""
        try:
            # Login
            resp = self._client.post(
                f"{self._base_url}/api/auth/login",
                json={"email": self._config.email, "password": self._config.password},
            )
            resp.raise_for_status()
            tokens = resp.json()
            self._access_token = tokens["access_token"]
            self._refresh_token = tokens["refresh_token"]

            # Workspace-ID holen (erster Workspace)
            resp = self._client.get(
                f"{self._base_url}/api/workspaces",
                headers=self._auth_headers(),
            )
            resp.raise_for_status()
            workspaces = resp.json()
            if not workspaces:
                return False
            self._workspace_id = workspaces[0]["id"]
            return True

        except httpx.HTTPError:
            return False

    def upload_document(self, file_path: Path) -> dict | None:
        """Lädt ein Dokument hoch. Gibt die API-Response zurück oder None bei Fehler."""
        if not self._access_token or not self._workspace_id:
            return None

        try:
            with open(file_path, "rb") as f:
                resp = self._client.post(
                    f"{self._base_url}/api/documents/upload",
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "X-Workspace-Id": self._workspace_id,
                    },
                    files={"file": (file_path.name, f)},
                )

            if resp.status_code == 401:
                # Token abgelaufen — refresh versuchen
                if self._refresh():
                    return self.upload_document(file_path)
                return None

            resp.raise_for_status()
            return resp.json()

        except httpx.HTTPError:
            return None

    def _auth_headers(self) -> dict:
        headers = {}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        if self._workspace_id:
            headers["X-Workspace-Id"] = self._workspace_id
        return headers

    def _refresh(self) -> bool:
        """Access-Token erneuern via Refresh-Token."""
        if not self._refresh_token:
            return False
        try:
            resp = self._client.post(
                f"{self._base_url}/api/auth/refresh",
                json={"refresh_token": self._refresh_token},
            )
            resp.raise_for_status()
            tokens = resp.json()
            self._access_token = tokens["access_token"]
            self._refresh_token = tokens["refresh_token"]
            return True
        except httpx.HTTPError:
            return False

    @property
    def workspace_id(self) -> str | None:
        return self._workspace_id

    def close(self) -> None:
        self._client.close()
