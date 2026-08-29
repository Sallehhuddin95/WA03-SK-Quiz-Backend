"""Pembantu keselamatan: hashing kata laluan dan token sesi.

Mengikut ADR 0006, kata laluan di-hash dengan Argon2 melalui pwdlib,
token sesi dijana secara rawak dan hanya hash SHA-256 disimpan dalam DB.
"""

import hashlib
import secrets

from pwdlib import PasswordHash

from app.core.config import get_settings

_settings = get_settings()

SESSION_COOKIE_NAME = _settings.session_cookie_name

_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hasher.verify(password, password_hash)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
