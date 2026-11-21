def register_and_login(
    client,
    email: str,
    full_name: str,
) -> str:
    """Register an employee and return their access token."""

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": full_name,
            "password": "SecurePassword123",
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "SecurePassword123",
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def create_ticket(client, token: str, subject: str):
    """Create a ticket using the supplied access token."""

    return client.post(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject": subject,
            "description": "This is a test ticket description.",
            "category": "hardware",
            "priority": "high",
        },
    )


def test_create_ticket_success(client):
    token = register_and_login(
        client,
        "employee1@example.com",
        "Employee One",
    )

    response = create_ticket(
        client,
        token,
        "Laptop not starting",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["subject"] == "Laptop not starting"
    assert data["category"] == "hardware"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert data["assignee_id"] is None


def test_employee_can_view_own_ticket(client):
    token = register_and_login(
        client,
        "employee2@example.com",
        "Employee Two",
    )

    creation = create_ticket(
        client,
        token,
        "Keyboard not working",
    )

    ticket_id = creation.json()["id"]

    response = client.get(
        f"/api/v1/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == ticket_id


def test_employee_cannot_view_another_employees_ticket(client):
    token_one = register_and_login(
        client,
        "employee3@example.com",
        "Employee Three",
    )

    token_two = register_and_login(
        client,
        "employee4@example.com",
        "Employee Four",
    )

    creation = create_ticket(
        client,
        token_one,
        "Monitor not working",
    )

    ticket_id = creation.json()["id"]

    response = client.get(
        f"/api/v1/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {token_two}"},
    )

    assert response.status_code == 404


def test_unauthenticated_user_cannot_create_ticket(client):
    response = client.post(
        "/api/v1/tickets/",
        json={
            "subject": "Network connection issue",
            "description": "Unable to connect to the office network.",
            "category": "network",
            "priority": "normal",
        },
    )

    assert response.status_code == 401


def test_employee_can_only_see_own_tickets(client):
    token_one = register_and_login(
        client,
        "employee5@example.com",
        "Employee Five",
    )

    token_two = register_and_login(
        client,
        "employee6@example.com",
        "Employee Six",
    )

    create_ticket(client, token_one, "First employee ticket")
    create_ticket(client, token_two, "Second employee ticket")

    response = client.get(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {token_one}"},
    )

    assert response.status_code == 200

    tickets = response.json()

    assert len(tickets) == 1
    assert tickets[0]["subject"] == "First employee ticket"
