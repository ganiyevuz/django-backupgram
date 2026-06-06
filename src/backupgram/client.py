from __future__ import annotations

import contextlib

import httpx


class BackupgramAPIError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.message = message
        self.status = status


class BackupgramClient:
    def __init__(self, base_url, token, *, verify=True, timeout=30, transport=None):
        self._client = httpx.Client(
            base_url=str(base_url).rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            verify=verify,
            timeout=timeout,
            transport=transport,
        )

    @classmethod
    def from_server(cls, server, *, transport=None):
        return cls(
            server.base_url,
            server.token,
            verify=server.verify_tls,
            timeout=server.timeout,
            transport=transport,
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _request(self, method, path, *, json=None, params=None):
        try:
            resp = self._client.request(method, path, json=json, params=params)
        except httpx.HTTPError as exc:
            raise BackupgramAPIError(f"request failed: {exc}") from exc
        if resp.status_code >= 400:
            message = resp.text
            with contextlib.suppress(ValueError):
                message = resp.json().get("error", message)
            raise BackupgramAPIError(message, status=resp.status_code)
        return resp

    # --- read ---

    def reachable(self) -> bool:
        try:
            self._request("GET", "/healthz")
            return True
        # reachability must never raise (bad URL, TLS, network, API error)
        except Exception:
            return False

    def status(self) -> dict:
        return self._request("GET", "/status").json()

    def list_backups(self) -> list:
        return self._request("GET", "/backups").json().get("backups", [])

    def list_jobs(self) -> list:
        return self._request("GET", "/jobs").json().get("jobs", [])

    def get_job(self, job_id) -> dict:
        return self._request("GET", f"/jobs/{job_id}").json()

    def get_config(self) -> dict:
        return self._request("GET", "/config").json().get("config", {})

    def iter_backup(self, slot, name, chunk_size=1024 * 1024):
        with self._client.stream("GET", f"/backups/{slot}/{name}") as resp:
            if resp.status_code >= 400:
                resp.read()
                message = resp.text
                with contextlib.suppress(ValueError):
                    message = resp.json().get("error", message)
                raise BackupgramAPIError(message, status=resp.status_code)
            yield from resp.iter_bytes(chunk_size)

    # --- mutate ---

    def trigger_backup(self) -> dict:
        return self._request("POST", "/backup").json()

    def restore(
        self,
        *,
        file=None,
        telegram_message_id=None,
        target_db,
        confirm=True,
    ) -> dict:
        if (file is None) == (telegram_message_id is None):
            raise BackupgramAPIError(
                "provide exactly one of file or telegram_message_id"
            )
        body: dict = {"target_db": target_db, "confirm": confirm}
        if file is not None:
            body["file"] = file
        else:
            body["telegram_message_id"] = int(telegram_message_id)
        return self._request("POST", "/restore", json=body).json()

    def delete_backup(self, slot, name) -> dict:
        return self._request(
            "DELETE", f"/backups/{slot}/{name}", params={"confirm": "true"}
        ).json()

    def patch_config(self, mapping) -> dict:
        return self._request("PATCH", "/config", json=mapping).json()

    def delete_config(self, key) -> dict:
        return self._request("DELETE", f"/config/{key}").json()
