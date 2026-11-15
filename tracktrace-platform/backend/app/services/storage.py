"""Document storage abstraction. Local disk for development, S3-compatible object storage for production."""
import re
from pathlib import Path
from typing import Protocol

from app.core.config import settings
from app.core.errors import err

ALLOWED = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK\x03\x04"),
    ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"PK\x03\x04"),
    ".csv": ("text/csv", None),
    ".txt": ("text/plain", None),
}


def sanitize_filename(name: str) -> str:
    base = Path(name.replace("\\", "/")).name
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" .")[:150]
    return base or "file"


def validate_upload(filename: str, data: bytes) -> tuple[str, str]:
    """Returns (extension, content_type) or raises. Trusts neither the client MIME type nor the extension alone."""
    if not data:
        raise err(422, "FILE_EMPTY", "The file is empty.")
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise err(413, "FILE_TOO_LARGE", f"Files can be up to {settings.MAX_UPLOAD_MB} MB.")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED:
        raise err(422, "FILE_TYPE_NOT_ALLOWED", "This file type is not allowed. Use PDF, PNG, JPG, DOCX, XLSX, CSV or TXT.")
    content_type, magic = ALLOWED[ext]
    if magic is not None and not data.startswith(magic):
        raise err(422, "FILE_CONTENT_MISMATCH", "The file content does not match its extension.")
    if magic is None:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise err(422, "FILE_CONTENT_MISMATCH", "The file content does not match its extension.") from exc
        if b"\x00" in data:
            raise err(422, "FILE_CONTENT_MISMATCH", "The file content does not match its extension.")
    return ext, content_type


class Storage(Protocol):
    def save(self, key: str, data: bytes, content_type: str) -> None: ...
    def read(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root)):  # path traversal guard
            raise ValueError("Invalid storage key")
        return p

    def save(self, key: str, data: bytes, content_type: str) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


class S3Storage:
    """S3-compatible storage (AWS S3, Cloudflare R2, Backblaze...). NOT exercised by automated tests in this repo."""

    def __init__(self):
        import boto3  # lazy import
        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            "s3", region_name=settings.S3_REGION or None, endpoint_url=settings.S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID or None, aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY or None)

    def save(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type, ServerSideEncryption="AES256") \
            if not settings.S3_ENDPOINT_URL else self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def read(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = S3Storage() if settings.STORAGE_BACKEND == "s3" else LocalStorage(settings.UPLOAD_DIR)
    return _storage
