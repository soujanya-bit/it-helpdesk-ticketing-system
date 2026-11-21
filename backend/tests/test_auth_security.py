from datetime import timedelta

from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def create_test_user(db_session, email, is_active=True):
    """Create a test employee directly in the database."""

    user = User(
        email=email,
        full_name="Security Test Employee",
        password_hash=hash_password("SecurePassword123"),
        role=UserRole.EMPLOYEE,
        is_active=is_active,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_invalid_token_returns_401(client):
    """An invalid JWT must not authenticate a user."""

    response = client.get(
        "/api/v1/tickets/",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401


def test_expired_token_returns_401(client, db_session):
    """An expired JWT must not authenticate a user."""

    user = create_test_user(
        db_session,
        "expired_token@example.com",
    )

    expired_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_access_protected_endpoint(
    client,
    db_session,
):
    """A deactivated account must not access protected resources."""

    user = create_test_user(
        db_session,
        "inactive_user@example.com",
        is_active=False,
    )

    token = create_access_token(
        subject=str(user.id),
    )

    response = client.get(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("This account has been deactivated.")


def test_inactive_user_cannot_login(client, db_session):
    """A deactivated account must not obtain a new access token."""

    user = create_test_user(
        db_session,
        "inactive_login@example.com",
        is_active=False,
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": user.email,
            "password": "SecurePassword123",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("This account has been deactivated.")


def test_missing_token_returns_401(client):
    """Protected endpoints must reject requests without a token."""

    response = client.get("/api/v1/tickets/")

    assert response.status_code == 401
