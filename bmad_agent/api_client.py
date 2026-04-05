"""API-Client — Authentifizierung und Dokument-Upload."""

from __future__ import annotations

from pathlib import Path

import httpx

from bmad_agent.config import save_config


class ApiClient:
    """Verbindet sich mit dem BMAD-Doc-AI Server."""

    def __init__(self, config: dict) -> None:
        self._config = config
        self._base_url = config["server_url"].rstrip("/")
        self._access_token: str | None = config.get("access_token") or None
        self._refresh_token: str | None = config.get("refresh_token") or None
        self._workspace_id: str | None = config.get("workspace_id") or None
        self._client = httpx.Client(timeout=60.0)

    def login(self) -> bool:
        """Anmelden — je nach auth_method."""
        method = self._config.get("auth_method", "password")

        if method == "google" and self._access_token:
            # Google: Token ist schon da, nur Workspace holen
            return self._fetch_workspace()

        if method == "password":
            return self._password_login()

        return False

    def _password_login(self) -> bool:
        """Login mit E-Mail/Passwort."""
        try:
            resp = self._client.post(
                f"{self._base_url}/api/auth/login",
                json={
                    "email": self._config["email"],
                    "password": self._config["password"],
                },
            )
            resp.raise_for_status()
            tokens = resp.json()
            self._access_token = tokens["access_token"]
            self._refresh_token = tokens["refresh_token"]

            # Tokens in Config speichern
            self._config["access_token"] = self._access_token
            self._config["refresh_token"] = self._refresh_token
            save_config(self._config)

            return self._fetch_workspace()
        except httpx.HTTPError:
            return False

    def _fetch_workspace(self) -> bool:
        """Workspace-ID holen (erster Workspace)."""
        if self._workspace_id:
            return True

        try:
            resp = self._client.get(
                f"{self._base_url}/api/workspaces",
                headers=self._auth_headers(),
            )
            if resp.status_code == 401:
                # Token abgelaufen
                if self._refresh():
                    return self._fetch_workspace()
                return False

            resp.raise_for_status()
            workspaces = resp.json()
            if not workspaces:
                return False

            self._workspace_id = workspaces[0]["id"]
            self._config["workspace_id"] = self._workspace_id
            self._config["workspace_name"] = workspaces[0].get("name", "")
            save_config(self._config)
            return True
        except httpx.HTTPError:
            return False

    def upload_document(self, file_path: Path) -> dict | None:
        """Lädt ein Dokument hoch."""
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
        """Access-Token erneuern."""
        if not self._refresh_token:
            # Bei Google-Login: kein Refresh möglich → neu einloggen nötig
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
            self._config["access_token"] = self._access_token
            self._config["refresh_token"] = self._refresh_token
            save_config(self._config)
            return True
        except httpx.HTTPError:
            return False

    @property
    def workspace_id(self) -> str | None:
        return self._workspace_id

    @property
    def workspace_name(self) -> str:
        return self._config.get("workspace_name", "")

    def close(self) -> None:
        self._client.close()
