import pytest


def register_employee(client):
    email = "query_validation@example.com"
    password = "SecurePassword123"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Query Validation Employee",
            "password": password,
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


@pytest.fixture
def auth_headers(client):
    token = register_employee(client)

    return {"Authorization": f"Bearer {token}"}


def test_ticket_list_rejects_negative_skip(client, auth_headers):
    response = client.get(
        "/api/v1/tickets/",
        params={"skip": -1},
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.parametrize("limit", [0, 101])
def test_ticket_list_rejects_invalid_limit(
    client,
    auth_headers,
    limit,
):
    response = client.get(
        "/api/v1/tickets/",
        params={"limit": limit},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_ticket_list_rejects_oversized_category(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/tickets/",
        params={"category": "a" * 101},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_ticket_list_rejects_oversized_search(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/tickets/",
        params={"search": "a" * 201},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_ticket_list_rejects_invalid_assignee_uuid(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/tickets/",
        params={"assignee_id": "not-a-valid-uuid"},
        headers=auth_headers,
    )

    assert response.status_code == 422
