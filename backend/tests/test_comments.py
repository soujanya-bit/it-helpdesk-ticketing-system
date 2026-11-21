
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


def create_test_ticket(client, token):
    response = client.post(
        "/api/v1/tickets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject": "Test network issue",
            "description": "The office network is unavailable.",
            "category": "network",
            "priority": "normal",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_employee_can_create_public_comment(client):
    token = register_employee(
        client,
        "comment_employee1@example.com",
    )

    ticket = create_test_ticket(client, token)

    response = client.post(
        f"/api/v1/tickets/{ticket['id']}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={"body": "I have restarted my computer."},
    )

    assert response.status_code == 201
    assert response.json()["body"] == "I have restarted my computer."
    assert response.json()["is_internal"] is False


def test_employee_cannot_create_internal_note(client):
    token = register_employee(
        client,
        "comment_employee2@example.com",
    )

    ticket = create_test_ticket(client, token)

    response = client.post(
        f"/api/v1/tickets/{ticket['id']}/internal-notes",
        headers={"Authorization": f"Bearer {token}"},
        json={"body": "Internal staff note."},
    )

    assert response.status_code == 403


def test_employee_cannot_see_internal_notes(
    client,
    db_session,
):
    employee_token = register_employee(
        client,
        "comment_employee3@example.com",
    )

    ticket = create_test_ticket(client, employee_token)

    agent = create_staff(
        db_session,
        "comment_agent1@example.com",
        UserRole.AGENT,
    )

    # Assign the ticket to the agent.
    assignment = client.patch(
        f"/api/v1/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": (
                f"Bearer {create_access_token(str(create_staff(db_session, 'comment_admin1@example.com', UserRole.ADMIN).id))}"
            )
        },
        json={"assignee_id": str(agent.id)},
    )

    assert assignment.status_code == 200

    # Agent creates an internal note.
    agent_token = create_access_token(str(agent.id))

    note_response = client.post(
        f"/api/v1/tickets/{ticket['id']}/internal-notes",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"body": "Internal diagnostic information."},
    )

    assert note_response.status_code == 201

    # Employee retrieves comments.
    comments_response = client.get(
        f"/api/v1/tickets/{ticket['id']}/comments",
        headers={"Authorization": f"Bearer {employee_token}"},
    )

    assert comments_response.status_code == 200

    comments = comments_response.json()

    assert all(
        comment["is_internal"] is False
        for comment in comments
    )

    assert not any(
        comment["body"] == "Internal diagnostic information."
        for comment in comments
    )


def test_agent_can_see_internal_notes(
    client,
    db_session,
):
    employee_token = register_employee(
        client,
        "comment_employee4@example.com",
    )

    ticket = create_test_ticket(client, employee_token)

    admin = create_staff(
        db_session,
        "comment_admin2@example.com",
        UserRole.ADMIN,
    )

    agent = create_staff(
        db_session,
        "comment_agent2@example.com",
        UserRole.AGENT,
    )

    assignment = client.patch(
        f"/api/v1/tickets/{ticket['id']}/assign",
        headers={
            "Authorization": f"Bearer {create_access_token(str(admin.id))}"
        },
        json={"assignee_id": str(agent.id)},
    )

    assert assignment.status_code == 200

    agent_token = create_access_token(str(agent.id))

    note_response = client.post(
        f"/api/v1/tickets/{ticket['id']}/internal-notes",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={"body": "Internal diagnostic information."},
    )

    assert note_response.status_code == 201

    comments_response = client.get(
        f"/api/v1/tickets/{ticket['id']}/comments",
        headers={"Authorization": f"Bearer {agent_token}"},
    )

    assert comments_response.status_code == 200

    comments = comments_response.json()

    assert any(
        comment["is_internal"] is True
        and comment["body"] == "Internal diagnostic information."
        for comment in comments
    )
