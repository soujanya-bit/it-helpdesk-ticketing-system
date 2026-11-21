
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


# Configure Argon2id password hashing.
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using Argon2id.

    The original password is never stored in the database.
    """
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against its stored hash.
    """
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    The subject identifies the user associated with the token.
    """

    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.access_token_expire_minutes
        )

    expire = now + expires_delta

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256",
    )

    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Raises ValueError if the token is invalid or expired.
    """

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
        )

        if not payload.get("sub"):
            raise ValueError("Token is missing its subject.")

        return payload

    except jwt.InvalidTokenError as exc:
        raise ValueError(
            "Invalid or expired access token."
        ) from exc
