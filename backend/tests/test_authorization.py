from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole


def create_staff_user(db_session, email, role):
    """Create an agent or administrator directly in the test database."""

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
    """Register an employee and create a ticket."""

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
            "priority": "high",
        },
    )

    assert ticket_response.status_code == 201

    return employee_token, ticket_response.json()


def test_employee_cannot_assign_ticket(client, db_session):
    _, ticket = create_employee_and_ticket(
        client,
        "employee_auth1@example.com",
    )

    agent = create_staff_user(
        db_session,
        "agent_auth1@example.com",
        UserRole.AGENT,
    )

    employee_login = client.post(
        "/api/v1/auth/login",
        data={
            "username": "employee_auth1@example.com",
            "password": "SecurePassword123",
        },
    )

    employee_token = employee_login.json()["access_token"]

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/assign",
        headers={"Authorization": f"Bearer {employee_token}"},
        json={
            "assignee_id": str(agent.id),
        },
    )

    assert response.status_code == 403


def test_agent_cannot_assign_ticket(client, db_session):
    _, ticket = create_employee_and_ticket(
        client,
        "employee_auth2@example.com",
    )

    agent = create_staff_user(
        db_session,
        "agent_auth2@example.com",
        UserRole.AGENT,
    )

    another_agent = create_staff_user(
        db_session,
        "agent_auth3@example.com",
        UserRole.AGENT,
    )

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/assign",
        headers={"Authorization": f"Bearer {get_token(agent)}"},
        json={
            "assignee_id": str(another_agent.id),
        },
    )

    assert response.status_code == 403


def test_admin_can_assign_ticket(client, db_session):
    _, ticket = create_employee_and_ticket(
        client,
        "employee_auth3@example.com",
    )

    admin = create_staff_user(
        db_session,
        "admin_auth1@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "agent_auth4@example.com",
        UserRole.AGENT,
    )

    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/assign",
        headers={"Authorization": f"Bearer {get_token(admin)}"},
        json={
            "assignee_id": str(agent.id),
        },
    )

    assert response.status_code == 200
    assert response.json()["assignee_id"] == str(agent.id)


def test_assigned_agent_can_change_ticket_status(
    client,
    db_session,
):
    _, ticket = create_employee_and_ticket(
        client,
        "employee_auth4@example.com",
    )

    admin = create_staff_user(
        db_session,
        "admin_auth2@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "agent_auth5@example.com",
        UserRole.AGENT,
    )

    # Administrator assigns the ticket.
    assignment = client.patch(
        f"/api/v1/tickets/{ticket['id']}/assign",
        headers={"Authorization": f"Bearer {get_token(admin)}"},
        json={
            "assignee_id": str(agent.id),
        },
    )

    assert assignment.status_code == 200

    # Assigned agent moves the ticket to in_progress.
    response = client.patch(
        f"/api/v1/tickets/{ticket['id']}/status",
        headers={"Authorization": f"Bearer {get_token(agent)}"},
        json={
            "status": "in_progress",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
