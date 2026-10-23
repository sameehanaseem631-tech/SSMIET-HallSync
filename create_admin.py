
from getpass import getpass

from app.database import SessionLocal
from app.models import User
from app.utils.security import hash_password


def main():
    full_name = input("Admin full name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass("Create admin password: ")

    if not full_name or not email or not password:
        print("Name, email and password are required.")
        return

    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            print("This email already exists. Use a different email.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("Admin account created successfully!")

    except Exception as error:
        db.rollback()
        print("Could not create admin:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()
