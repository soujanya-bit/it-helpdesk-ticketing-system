
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.user import User, UserRole


def create_comment(
    db: Session,
    ticket: Ticket,
    author: User,
    body: str,
    is_internal: bool = False,
) -> Comment:
    """
    Create a public comment or an internal staff note.
    """

    if is_internal and author.role == UserRole.EMPLOYEE:
        raise PermissionError(
            "Employees cannot create internal notes."
        )

    comment = Comment(
        ticket_id=ticket.id,
        author_id=author.id,
        body=body,
        is_internal=is_internal,
    )

    try:
        db.add(comment)
        db.commit()
        db.refresh(comment)

        return comment

    except Exception:
        db.rollback()
        raise


def list_comments(
    db: Session,
    ticket: Ticket,
    current_user: User,
) -> list[Comment]:
    """
    Retrieve comments based on the user's role.

    Employees can only see public comments.
    Agents and administrators can see all comments.
    """

    query = (
        select(Comment)
        .where(Comment.ticket_id == ticket.id)
        .order_by(Comment.created_at.asc())
    )

    if current_user.role == UserRole.EMPLOYEE:
        query = query.where(
            Comment.is_internal.is_(False)
        )

    return list(db.scalars(query).all())
