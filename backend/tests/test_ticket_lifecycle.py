from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def create_staff(db_session, email, role):
    user = User(
        email=email,
        full_name=f"Test {role.value.title()}",
        password_hash=hash_password("SecurePassword123"),
        role=role,
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


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


def create_ticket(client, employee_token):
    response = client.post(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "subject": "Laptop boot failure",
            "description": "The laptop fails to boot after an update.",
            "category": "hardware",
            "priority": "high",
        },
    )

    assert response.status_code == 201

    return response.json()


def assign_ticket(client, ticket_id, admin, agent):
    response = client.patch(
        f"/api/v1/tickets/{ticket_id}/assign",
        headers={"Authorization": (f"Bearer {create_access_token(str(admin.id))}")},
        json={
            "assignee_id": str(agent.id),
        },
    )

    assert response.status_code == 200

    return response


def test_ticket_lifecycle_success(client, db_session):
    employee_token = register_employee(
        client,
        "lifecycle_employee@example.com",
    )

    ticket = create_ticket(client, employee_token)

    admin = create_staff(
        db_session,
        "lifecycle_admin@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff(
        db_session,
        "lifecycle_agent@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    agent_headers = {"Authorization": f"Bearer {create_access_token(str(agent.id))}"}

    # Open -> In progress
    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/status",
        headers=agent_headers,
        json={"status": "in_progress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"

    # In progress -> Resolved
    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/status",
        headers=agent_headers,
        json={"status": "resolved"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
    assert response.json()["resolved_at"] is not None

    # Resolved -> Closed
    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/status",
        headers=agent_headers,
        json={"status": "closed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "closed"
    assert response.json()["closed_at"] is not None


def test_invalid_status_transition_is_rejected(
    client,
    db_session,
):
    employee_token = register_employee(
        client,
        "invalid_transition_employee@example.com",
    )

    ticket = create_ticket(client, employee_token)

    admin = create_staff(
        db_session,
        "invalid_transition_admin@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff(
        db_session,
        "invalid_transition_agent@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/status",
        headers={"Authorization": (f"Bearer {create_access_token(str(agent.id))}")},
        json={"status": "resolved"},
    )

    assert response.status_code == 400
    assert "Cannot transition" in response.json()["detail"]


def test_employee_cannot_change_ticket_status(client):
    employee_token = register_employee(
        client,
        "status_employee@example.com",
    )

    ticket = create_ticket(client, employee_token)

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/status",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={"status": "in_progress"},
    )

    assert response.status_code == 403


def test_ticket_history_records_lifecycle_events(
    client,
    db_session,
):
    employee_token = register_employee(
        client,
        "history_employee@example.com",
    )

    ticket = create_ticket(client, employee_token)

    admin = create_staff(
        db_session,
        "history_admin@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff(
        db_session,
        "history_agent@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    agent_headers = {"Authorization": f"Bearer {create_access_token(str(agent.id))}"}

    for new_status in ("in_progress", "resolved", "closed"):
        response = client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            headers=agent_headers,
            json={"status": new_status},
        )

        assert response.status_code == 200

    history_response = client.get(
        f"/api/v1/tickets/{ticket['id']}/history",
        headers={"Authorization": (f"Bearer {create_access_token(str(admin.id))}")},
    )

    assert history_response.status_code == 200

    history = history_response.json()

    event_types = [event["event_type"] for event in history]

    assert "created" in event_types
    assert "assigned" in event_types
    assert "status_changed" in event_types
    assert "resolved" in event_types
    assert "closed" in event_types

    # Verify that events are returned chronologically.
    timestamps = [event["created_at"] for event in history]

    assert timestamps == sorted(timestamps)
