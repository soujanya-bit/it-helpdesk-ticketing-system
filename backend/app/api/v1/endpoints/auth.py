
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserResponse,
)


router = APIRouter()


DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: DatabaseSession,
):
    """
    Register a new employee account.
    """

    # Check whether the email is already registered.
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create a new user.
    new_user = User(
        email=str(user_data.email),
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
        role=UserRole.EMPLOYEE,
        is_active=True,
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DatabaseSession,
):
    """
    Authenticate a user and return a JWT access token.

    The OAuth2 form field named 'username' receives the user's email.
    """

    # Find the account using the supplied email address.
    user = db.scalar(
        select(User).where(User.email == form_data.username)
    )

    # Use a generic error message to avoid revealing
    # whether an email address is registered.
    if user is None or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # Create a JWT containing the user's UUID.
    access_token = create_access_token(
        subject=str(user.id)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
