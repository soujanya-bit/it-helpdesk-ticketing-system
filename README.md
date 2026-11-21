# IT Helpdesk Ticketing System

A role-based IT Helpdesk Ticketing System built with FastAPI, SQLAlchemy and SQLite. The application provides ticket management, user authentication, role-based access control, internal staff notes and audit history.

## Technology Stack

**Backend**
- Python 3.14
- FastAPI
- SQLAlchemy 2.x
- Pydantic 2
- SQLite
- Alembic

**Security**
- JWT authentication
- Argon2id password hashing
- Role-based access control

**Testing**
- Pytest
- HTTPX
- FastAPI TestClient

## Features

- User registration and authentication
- Employee, agent and administrator roles
- Ticket creation and management
- Ticket assignment
- Ticket priority and status management
- Ticket filtering and pagination
- Public comments and private internal notes
- Ticket activity and audit history
- Database migrations
- Automated API and authorization tests

## Project Structure

helpdesk-system/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── scripts/
│   │   └── services/
│   ├── tests/
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
├── .env.example
├── .gitignore
└── README.md


## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/it-helpdesk-ticketing-system.git
cd it-helpdesk-ticketing-system
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the root `.env.example` to `.env`, then configure your own secret key and settings.

### 5. Apply database migrations

```powershell
alembic upgrade head
```

### 6. Start the backend

```powershell
uvicorn app.main:app --reload
```

API documentation:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/health

## Staff Account Provisioning

Public registration creates employee accounts only.

To provision an agent or administrator:

```powershell
python -m app.scripts.create_staff_user
```

## Running Tests

From the `backend` directory:

```powershell
pytest -v
```

Tests use an isolated in-memory SQLite database.

## API Overview

Base URL: `/api/v1`

| Endpoint | Purpose |
|---|---|
| `/auth/register` | Register an employee |
| `/auth/login` | Authenticate a user |
| `/tickets/` | Create and list tickets |
| `/tickets/{ticket_id}` | Retrieve a ticket |
| `/tickets/{ticket_id}/assign` | Assign a ticket |
| `/tickets/{ticket_id}/status` | Change ticket status |
| `/tickets/{ticket_id}/comments` | Manage public comments |
| `/tickets/{ticket_id}/internal-notes` | Create internal notes |
| `/tickets/{ticket_id}/history` | Retrieve audit history |

## Project Status

Backend implementation and initial automated testing are in progress. React frontend development, integration and deployment are planned next.

## License

To be determined.