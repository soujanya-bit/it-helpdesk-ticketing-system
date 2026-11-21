from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def create_staff_user() -> None:
    print("\n=== Helpdesk Staff Account Provisioning ===\n")

    email = input("Enter staff email: ").strip().lower()
    full_name = input("Enter full name: ").strip()

    print("\nAvailable roles:")
    print("1. Agent")
    print("2. Administrator")

    role_choice = input("Select role (1 or 2): ").strip()

    role_mapping = {
        "1": UserRole.AGENT,
        "2": UserRole.ADMIN,
    }

    role = role_mapping.get(role_choice)

    if role is None:
        print("Invalid role selection.")
        return

    password = getpass("Enter password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    if len(password) < 8 or len(password) > 128:
        print("Password must contain 8 to 128 characters.")
        return

    if not email or "@" not in email:
        print("Please enter a valid email address.")
        return

    if not full_name:
        print("Full name cannot be empty.")
        return

    db = SessionLocal()

    try:
        existing_user = db.scalar(select(User).where(User.email == email))

        if existing_user:
            print("An account with this email already exists.")
            return

        staff_user = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(staff_user)
        db.commit()
        db.refresh(staff_user)

        print("\nStaff account created successfully.")
        print(f"Email: {staff_user.email}")
        print(f"Role: {staff_user.role.value}")
        print(f"User ID: {staff_user.id}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_staff_user()
