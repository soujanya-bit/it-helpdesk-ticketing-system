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

    token = login.json()["access_token"]

    ticket_response = client.post(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject": "Laptop not starting",
            "description": "The laptop does not start.",
            "category": "hardware",
            "priority": "normal",
        },
    )

    assert ticket_response.status_code == 201

    return token, ticket_response.json()


def change_ticket_status(client, ticket_id, admin, new_status):
    """Change ticket status using an administrator."""

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {get_token(admin)}"},
        json={"status": new_status},
    )

    assert response.status_code == 200

    return response


def assign_ticket(client, ticket_id, admin, agent):
    """Assign a ticket to an agent."""

    response = client.patch(
        f"/api/v1/tickets/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {get_token(admin)}"},
        json={"assignee_id": str(agent.id)},
    )

    assert response.status_code == 200


def update_ticket(client, ticket_id, token):
    """Attempt to update ticket details."""

    return client.patch(
        f"/api/v1/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject": "Updated laptop issue",
        },
    )


def test_employee_can_edit_open_ticket(client):
    token, ticket = create_employee_and_ticket(
        client,
        "edit_open@example.com",
    )

    response = update_ticket(
        client,
        ticket["id"],
        token,
    )

    assert response.status_code == 200
    assert response.json()["subject"] == "Updated laptop issue"


def test_employee_can_edit_waiting_ticket(
    client,
    db_session,
):
    token, ticket = create_employee_and_ticket(
        client,
        "edit_waiting@example.com",
    )

    admin = create_staff_user(
        db_session,
        "edit_admin1@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "edit_agent1@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "in_progress",
    )

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "waiting_on_employee",
    )

    response = update_ticket(
        client,
        ticket["id"],
        token,
    )

    assert response.status_code == 200
    assert response.json()["subject"] == "Updated laptop issue"


def test_employee_cannot_edit_in_progress_ticket(
    client,
    db_session,
):
    token, ticket = create_employee_and_ticket(
        client,
        "edit_progress@example.com",
    )

    admin = create_staff_user(
        db_session,
        "edit_admin2@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "edit_agent2@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "in_progress",
    )

    response = update_ticket(
        client,
        ticket["id"],
        token,
    )

    assert response.status_code == 403


def test_employee_cannot_edit_resolved_ticket(
    client,
    db_session,
):
    token, ticket = create_employee_and_ticket(
        client,
        "edit_resolved@example.com",
    )

    admin = create_staff_user(
        db_session,
        "edit_admin3@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "edit_agent3@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "in_progress",
    )

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "resolved",
    )

    response = update_ticket(
        client,
        ticket["id"],
        token,
    )

    assert response.status_code == 403


def test_employee_cannot_edit_closed_ticket(
    client,
    db_session,
):
    token, ticket = create_employee_and_ticket(
        client,
        "edit_closed@example.com",
    )

    admin = create_staff_user(
        db_session,
        "edit_admin4@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "edit_agent4@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "in_progress",
    )

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "resolved",
    )

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "closed",
    )

    response = update_ticket(
        client,
        ticket["id"],
        token,
    )

    assert response.status_code == 403


def test_assigned_agent_can_edit_resolved_ticket(
    client,
    db_session,
):
    _, ticket = create_employee_and_ticket(
        client,
        "edit_agent_resolved@example.com",
    )

    admin = create_staff_user(
        db_session,
        "edit_admin5@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "edit_agent5@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "in_progress",
    )

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "resolved",
    )

    response = update_ticket(
        client,
        ticket["id"],
        get_token(agent),
    )

    assert response.status_code == 200
    assert response.json()["subject"] == "Updated laptop issue"


def test_admin_can_edit_closed_ticket(
    client,
    db_session,
):
    _, ticket = create_employee_and_ticket(
        client,
        "edit_admin_closed@example.com",
    )

    admin = create_staff_user(
        db_session,
        "edit_admin6@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff_user(
        db_session,
        "edit_agent6@example.com",
        UserRole.AGENT,
    )

    assign_ticket(client, ticket["id"], admin, agent)

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "in_progress",
    )

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "resolved",
    )

    change_ticket_status(
        client,
        ticket["id"],
        admin,
        "closed",
    )

    response = update_ticket(
        client,
        ticket["id"],
        get_token(admin),
    )

    assert response.status_code == 200
    assert response.json()["subject"] == "Updated laptop issue"


def test_unassigned_agent_cannot_edit_ticket(
    client,
    db_session,
):
    _, ticket = create_employee_and_ticket(
        client,
        "edit_unassigned@example.com",
    )

    agent = create_staff_user(
        db_session,
        "edit_agent7@example.com",
        UserRole.AGENT,
    )

    response = update_ticket(
        client,
        ticket["id"],
        get_token(agent),
    )

    assert response.status_code == 404
