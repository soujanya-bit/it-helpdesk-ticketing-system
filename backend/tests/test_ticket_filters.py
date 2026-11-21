def register_employee(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test Employee",
            "password": "SecurePassword123",
        },
    )

    assert response.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "SecurePassword123",
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def create_ticket(
    client,
    token,
    subject,
    category="hardware",
    priority="normal",
):
    return client.post(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject": subject,
            "description": "This is a test ticket description.",
            "category": category,
            "priority": priority,
        },
    )


def test_filter_tickets_by_status(client):
    token = register_employee(
        client,
        "filter_status@example.com",
    )

    create_ticket(
        client,
        token,
        "Open hardware ticket",
    )

    response = client.get(
        "/api/v1/tickets/",
        params={"status": "open"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "open"


def test_filter_tickets_by_priority(client):
    token = register_employee(
        client,
        "filter_priority@example.com",
    )

    create_ticket(
        client,
        token,
        "High priority ticket",
        priority="high",
    )

    create_ticket(
        client,
        token,
        "Low priority ticket",
        priority="low",
    )

    response = client.get(
        "/api/v1/tickets/",
        params={"priority": "high"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["priority"] == "high"


def test_filter_tickets_by_category(client):
    token = register_employee(
        client,
        "filter_category@example.com",
    )

    create_ticket(
        client,
        token,
        "Laptop hardware issue",
        category="hardware",
    )

    create_ticket(
        client,
        token,
        "Office network issue",
        category="network",
    )

    response = client.get(
        "/api/v1/tickets/",
        params={"category": "hardware"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["category"] == "hardware"


def test_search_tickets_by_subject(client):
    token = register_employee(
        client,
        "filter_search@example.com",
    )

    create_ticket(
        client,
        token,
        "Laptop not starting",
    )

    create_ticket(
        client,
        token,
        "Keyboard not working",
    )

    response = client.get(
        "/api/v1/tickets/",
        params={"search": "Laptop"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "Laptop" in response.json()[0]["subject"]


def test_ticket_pagination(client):
    token = register_employee(
        client,
        "filter_pagination@example.com",
    )

    first_ticket = create_ticket(
        client,
        token,
        "First pagination ticket",
    )

    second_ticket = create_ticket(
        client,
        token,
        "Second pagination ticket",
    )

    assert first_ticket.status_code == 201
    assert second_ticket.status_code == 201

    headers = {"Authorization": f"Bearer {token}"}

    first_page = client.get(
        "/api/v1/tickets/",
        params={"skip": 0, "limit": 1},
        headers=headers,
    )

    second_page = client.get(
        "/api/v1/tickets/",
        params={"skip": 1, "limit": 1},
        headers=headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1

    first_id = first_page.json()[0]["id"]
    second_id = second_page.json()[0]["id"]

    assert first_id != second_id


def test_employee_filtering_does_not_expose_other_tickets(client):
    employee_one = register_employee(
        client,
        "filter_employee1@example.com",
    )

    employee_two = register_employee(
        client,
        "filter_employee2@example.com",
    )

    create_ticket(
        client,
        employee_one,
        "Employee one laptop issue",
    )

    create_ticket(
        client,
        employee_two,
        "Employee two laptop issue",
    )

    response = client.get(
        "/api/v1/tickets/",
        params={"search": "laptop"},
        headers={"Authorization": f"Bearer {employee_one}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["subject"] == "Employee one laptop issue"
