from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def create_staff_user(db_session, email, role):
    """Create an agent or administrator in the test database."""

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


def get_token(user):
    """Generate an access token for a test user."""

    return create_access_token(subject=str(user.id))


def create_employee_and_ticket(client, email):
    """Register an employee and create a test ticket."""

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test Employee",
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

    employee_token = login.json()["access_token"]

    ticket_response = client.post(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "subject": "Test laptop issue",
            "description": "Laptop is not starting properly.",
            "category": "hardware",
            "priority": "normal",
        },
    )

    assert ticket_response.status_code == 201

    return employee_token, ticket_response.json()


def assign_ticket_to_agent(client, ticket_id, admin, agent):
    """Assign a ticket to an agent using an administrator."""

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {get_token(admin)}"},
        json={
            "assignee_id": str(agent.id),
        },
    )

    assert response.status_code == 200

    return response


def test_admin_can_change_ticket_priority(client, db_session):
    _, ticket = create_employee_and_ticket(
        client,
        "priority_employee1@example.com",
    )

    admin = create_staff_user(
        db_session,
        "priority_admin1@example.com",
        UserRole.ADMIN,
    )

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/priority",
        headers={"Authorization": f"Bearer {get_token(admin)}"},
        json={
            "priority": "urgent",
        },
    )

    assert response.status_code == 200
    assert response.json()["priority"] == "urgent"


def test_assigned_agent_can_change_ticket_priority(
    client,
    db_session,
):
    _, ticket = create_employee_and_ticket(
        client,
        "priority_employee2@example.com",
    )

    admin = create_staff_user(
        db_session,
        "priority_admin2@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "priority_agent1@example.com",
        UserRole.AGENT,
    )

    assign_ticket_to_agent(
        client,
        ticket["id"],
        admin,
        agent,
    )

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/priority",
        headers={"Authorization": f"Bearer {get_token(agent)}"},
        json={
            "priority": "high",
        },
    )

    assert response.status_code == 200
    assert response.json()["priority"] == "high"


def test_unassigned_agent_cannot_change_ticket_priority(
    client,
    db_session,
):
    _, ticket = create_employee_and_ticket(
        client,
        "priority_employee3@example.com",
    )

    agent = create_staff_user(
        db_session,
        "priority_agent2@example.com",
        UserRole.AGENT,
    )

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/priority",
        headers={"Authorization": f"Bearer {get_token(agent)}"},
        json={
            "priority": "urgent",
        },
    )

    assert response.status_code == 404


def test_employee_cannot_change_ticket_priority(
    client,
):
    employee_token, ticket = create_employee_and_ticket(
        client,
        "priority_employee4@example.com",
    )

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/priority",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "priority": "urgent",
        },
    )

    assert response.status_code == 403


def test_changing_to_same_priority_returns_bad_request(
    client,
    db_session,
):
    _, ticket = create_employee_and_ticket(
        client,
        "priority_employee5@example.com",
    )

    admin = create_staff_user(
        db_session,
        "priority_admin3@example.com",
        UserRole.ADMIN,
    )

    headers = {"Authorization": f"Bearer {get_token(admin)}"}

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/priority",
        headers=headers,
        json={
            "priority": "normal",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Ticket already has the requested priority."


def test_priority_change_is_recorded_in_ticket_history(
    client,
    db_session,
):
    _, ticket = create_employee_and_ticket(
        client,
        "priority_employee6@example.com",
    )

    admin = create_staff_user(
        db_session,
        "priority_admin4@example.com",
        UserRole.ADMIN,
    )

    headers = {"Authorization": f"Bearer {get_token(admin)}"}

    update_response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/priority",
        headers=headers,
        json={
            "priority": "urgent",
        },
    )

    assert update_response.status_code == 200

    history_response = client.get(
        f"/api/v1/tickets/{ticket['id']}/history",
        headers=headers,
    )

    assert history_response.status_code == 200

    history = history_response.json()

    priority_events = [
        event for event in history if event["event_type"] == "priority_changed"
    ]

    assert len(priority_events) == 1

    event = priority_events[0]

    assert event["old_values"]["priority"] == "normal"
    assert event["new_values"]["priority"] == "urgent"
    assert event["actor_id"] == str(admin.id)
