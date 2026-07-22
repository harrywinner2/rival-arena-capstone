from __future__ import annotations

import hashlib
import json
import os
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import requests


def require_job_id(value: str) -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    if not value or len(value) > 96 or any(char not in allowed for char in value):
        raise ValueError("job id must be 1-96 characters from [A-Za-z0-9_-]")
    return value


class ResultClient:
    def __init__(self, base_url: str, token: str, job_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        if not self.base_url.startswith("https://"):
            raise ValueError("receiver must use HTTPS")
        if not token:
            raise ValueError("receiver token is required")
        self.token = token
        self.job_id = require_job_id(job_id)

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def status(self, stage: str, payload: dict[str, Any]) -> None:
        body = {"job_id": self.job_id, "stage": stage, "payload": payload}
        response = requests.post(
            f"{self.base_url}/v1/status",
            headers=self.headers,
            json=body,
            timeout=30,
        )
        response.raise_for_status()

    def upload(self, path: Path, kind: str = "artifact") -> dict[str, Any]:
        path = path.resolve()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open("rb") as handle:
            response = requests.put(
                f"{self.base_url}/v1/jobs/{self.job_id}/artifacts/{path.name}",
                headers={**self.headers, "X-Artifact-SHA256": digest, "X-Artifact-Kind": kind},
                data=handle,
                timeout=600,
            )
        response.raise_for_status()
        return response.json()


def bundle_directory(source: Path, output: Path) -> Path:
    source = source.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.add(path, arcname=path.relative_to(source))
    return output


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)
