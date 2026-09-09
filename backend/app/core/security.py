"""Small, dependency-light cryptographic helpers for authentication."""

import hashlib
import secrets

import bcrypt


def hash_password(password: str) -> str:
    """Return a bcrypt password hash; callers must never log the input."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"
