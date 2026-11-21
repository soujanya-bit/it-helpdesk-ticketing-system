
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.comment_service import create_comment, list_comments

from app.api.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.ticket import (
    TicketAssignment,
    TicketCreate,
    TicketResponse,
    TicketUpdate,
    TicketStatusUpdate,
)
from app.models.ticket import (
    TicketPriority,
    TicketStatus,
)
from app.schemas.ticket_history import TicketHistoryResponse
from app.services.ticket_service import (
    assign_ticket,
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket_details,
    update_ticket_status,
    get_ticket_history,
)


router = APIRouter()

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_ticket(
    ticket_data: TicketCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """Create a ticket for the authenticated user."""

    return create_ticket(
        db=db,
        requester=current_user,
        ticket_data=ticket_data,
    )



@router.get(
    "/",
    response_model=list[TicketResponse],
)
def get_all_tickets(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: TicketStatus | None = Query(
        default=None,
        alias="status",
    ),
    priority: TicketPriority | None = None,
    category: str | None = None,
    search: str | None = None,
    assignee_id: UUID | None = None,
):
    try:
        return list_tickets(
            db=db,
            current_user=current_user,
            skip=skip,
            limit=limit,
            status=status_filter,
            priority=priority,
            category=category,
            search=search,
            assignee_id=assignee_id,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from None



@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_single_ticket(
    ticket_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """Retrieve one ticket if the user has permission to view it."""

    try:
        return get_ticket(
            db=db,
            ticket_id=ticket_id,
            current_user=current_user,
        )

    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        ) from None


@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def update_existing_ticket(
    ticket_id: UUID,
    ticket_data: TicketUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """
    Update ticket details.

    Employees can update their own tickets.
    Agents can update tickets assigned to them.
    Administrators can update any ticket.
    """

    try:
        ticket = get_ticket(
            db=db,
            ticket_id=ticket_id,
            current_user=current_user,
        )

        return update_ticket_details(
            db=db,
            ticket=ticket,
            actor=current_user,
            ticket_data=ticket_data,
        )

    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        ) from None


@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
)
def assign_existing_ticket(
    ticket_id: UUID,
    assignment: TicketAssignment,
    db: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN)),
    ],
):
    """Assign a ticket to an agent. Administrators only."""

    try:
        ticket = get_ticket(
            db=db,
            ticket_id=ticket_id,
            current_user=current_user,
        )

        return assign_ticket(
            db=db,
            ticket=ticket,
            agent_id=assignment.assignee_id,
            actor=current_user,
        )

    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        ) from None

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
)
def change_ticket_status(
    ticket_id: UUID,
    status_data: TicketStatusUpdate,
    db: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(
            require_roles(UserRole.AGENT, UserRole.ADMIN)
        ),
    ],
):
    try:
        ticket = get_ticket(
            db=db,
            ticket_id=ticket_id,
            current_user=current_user,
        )

        return update_ticket_status(
            db=db,
            ticket=ticket,
            new_status=status_data.status,
            actor=current_user,
        )

    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        ) from None

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

@router.get(
    "/{ticket_id}/history",
    response_model=list[TicketHistoryResponse],
)
def read_ticket_history(
    ticket_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    try:
        # Verify that the current user can access this ticket.
        get_ticket(
            db=db,
            ticket_id=ticket_id,
            current_user=current_user,
        )

        return get_ticket_history(
            db=db,
            ticket_id=ticket_id,
        )

    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        ) from None

@router.post(
    "/{ticket_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_ticket_comment(
    ticket_id: UUID,
    comment_data: CommentCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    try:
        ticket = get_ticket(
            db=db,
            ticket_id=ticket_id,
            current_user=current_user,
        )

        return create_comment(
            db=db,
            ticket=ticket,
            author=current_user,
            body=comment_data.body,
            is_internal=False,
        )

    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        ) from None


@router.get(
    "/{ticket_id}/comments",
    response_model=list[CommentResponse],
)
def read_ticket_comments(
    ticket_id: UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    try:
        ticket = get_ticket(
            db=db,
            ticket_id=ticket_id,
            current_user=current_user,
        )

        return list_comments(
            db=db,
            ticket=ticket,
            current_user=current_user,
        )

    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        ) from None

@router.post(
    "/{ticket_id}/internal-notes",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_internal_note(
    ticket_id: UUID,
    comment_data: CommentCreate,
    db: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(
            require_roles(UserRole.AGENT, UserRole.ADMIN)
        ),
    ],
):
    try:
        ticket = get_ticket(
            db=db,
            ticket_id=ticket_id,
            current_user=current_user,
        )

        return create_comment(
            db=db,
            ticket=ticket,
            author=current_user,
            body=comment_data.body,
            is_internal=True,
        )

    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        ) from None

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from None
