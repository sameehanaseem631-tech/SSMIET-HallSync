
from getpass import getpass

from app.database import SessionLocal
from app.models import User
from app.utils.security import hash_password


def main():
    print("\n=== SSMIET HallSync AI - Create User ===")

    full_name = input("Enter full name: ").strip()
    email = input("Enter email: ").strip().lower()
    role = input("Enter role (admin/faculty): ").strip().lower()

    if not full_name or not email:
        print("Error: Name and email are required.")
        return

    if role not in {"admin", "faculty"}:
        print("Error: Role must be admin or faculty.")
        return

    password = getpass("Enter password (minimum 8 characters): ")

    if len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        return

    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("Error: This email is already registered.")
            return

        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()

        print(f"\nUser created successfully!")
        print(f"Name: {full_name}")
        print(f"Email: {email}")
        print(f"Role: {role}")

    except Exception as error:
        db.rollback()
        print(f"Error creating user: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
