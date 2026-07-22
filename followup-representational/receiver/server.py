from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

JOB_RE = re.compile(r"^[A-Za-z0-9_-]{1,96}$")
FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class Receiver(BaseHTTPRequestHandler):
    server_version = "L4Receiver/1"

    @property
    def root(self) -> Path:
        return self.server.root  # type: ignore[attr-defined]

    @property
    def token(self) -> str:
        return self.server.token  # type: ignore[attr-defined]

    @property
    def max_bytes(self) -> int:
        return self.server.max_bytes  # type: ignore[attr-defined]

    def _json(self, status: int, payload: dict) -> None:
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {self.token}"
        return hmac.compare_digest(supplied, expected)

    def _length(self) -> int:
        try:
            value = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            return -1
        return value

    def _reject_unless_authorized(self) -> bool:
        if self._authorized():
            return False
        self._json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
        return True

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/healthz":
            self._json(HTTPStatus.OK, {"status": "ok"})
        else:
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if self._reject_unless_authorized():
            return
        if urlparse(self.path).path != "/v1/status":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        length = self._length()
        if length < 0 or length > 1_000_000:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid size"})
            return
        try:
            body = json.loads(self.rfile.read(length))
            job_id = body["job_id"]
            if not JOB_RE.fullmatch(job_id):
                raise ValueError("invalid job id")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid status payload"})
            return
        record = {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "stage": body.get("stage"),
            "payload": body.get("payload", {}),
        }
        directory = self.root / job_id
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "status.jsonl").open("a") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        self._json(HTTPStatus.ACCEPTED, {"accepted": True})

    def do_PUT(self) -> None:
        if self._reject_unless_authorized():
            return
        match = re.fullmatch(r"/v1/jobs/([^/]+)/artifacts/([^/]+)", urlparse(self.path).path)
        if not match or not JOB_RE.fullmatch(match[1]) or not FILE_RE.fullmatch(match[2]):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid artifact path"})
            return
        length = self._length()
        if length < 0 or length > self.max_bytes:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid size"})
            return
        expected = self.headers.get("X-Artifact-SHA256", "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "sha256 required"})
            return
        directory = self.root / match[1] / "artifacts"
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / match[2]
        digest = hashlib.sha256()
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as handle:
            remaining = length
            while remaining:
                block = self.rfile.read(min(1024 * 1024, remaining))
                if not block:
                    break
                handle.write(block)
                digest.update(block)
                remaining -= len(block)
            temporary = Path(handle.name)
        if remaining or not hmac.compare_digest(digest.hexdigest(), expected):
            temporary.unlink(missing_ok=True)
            self._json(HTTPStatus.BAD_REQUEST, {"error": "digest mismatch"})
            return
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != expected:
            temporary.unlink(missing_ok=True)
            self._json(HTTPStatus.CONFLICT, {"error": "artifact already exists"})
            return
        os.replace(temporary, destination)
        self._json(HTTPStatus.CREATED, {"stored": str(destination.relative_to(self.root)), "sha256": expected})

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    token = os.environ.get("L4_RECEIVER_TOKEN", "")
    if len(token) < 32:
        raise SystemExit("L4_RECEIVER_TOKEN must contain at least 32 characters")
    root = Path(os.environ.get("L4_RECEIVER_ROOT", "./receiver-data")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    host = os.environ.get("L4_RECEIVER_HOST", "127.0.0.1")
    port = int(os.environ.get("L4_RECEIVER_PORT", "8091"))
    server = ThreadingHTTPServer((host, port), Receiver)
    server.root = root  # type: ignore[attr-defined]
    server.token = token  # type: ignore[attr-defined]
    server.max_bytes = int(os.environ.get("L4_RECEIVER_MAX_BYTES", str(2 * 1024**3)))  # type: ignore[attr-defined]
    server.serve_forever()


if __name__ == "__main__":
    main()
