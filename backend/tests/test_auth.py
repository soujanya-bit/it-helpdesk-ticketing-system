def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "employee@example.com",
            "full_name": "Test Employee",
            "password": "SecurePassword123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "employee@example.com"
    assert data["full_name"] == "Test Employee"
    assert data["role"] == "employee"
    assert data["is_active"] is True

    # Password information must never be returned.
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    user_data = {
        "email": "duplicate@example.com",
        "full_name": "Test Employee",
        "password": "SecurePassword123",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_success(client):
    # First, register an account.
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "full_name": "Login Employee",
            "password": "SecurePassword123",
        },
    )

    # OAuth2PasswordRequestForm expects form data.
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@example.com",
            "password": "SecurePassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_invalid_password(client):
    # Register an account.
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpassword@example.com",
            "full_name": "Test Employee",
            "password": "SecurePassword123",
        },
    )

    # Attempt login with an incorrect password.
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrongpassword@example.com",
            "password": "IncorrectPassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "SomePassword123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."
