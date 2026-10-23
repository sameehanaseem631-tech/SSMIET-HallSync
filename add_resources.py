from app.database import SessionLocal
from app.models import Resource

db = SessionLocal()

try:
    resources = [
        Resource(
            hall_id=1,
            name="Wireless Microphone",
            category="Audio Equipment",
            quantity=4,
            is_available=True,
            notes="Wireless microphones for college events",
        ),
        Resource(
            hall_id=1,
            name="Sound System",
            category="Audio Equipment",
            quantity=2,
            is_available=True,
            notes="Speakers for meetings and cultural programmes",
        ),
        Resource(
            hall_id=3,
            name="Whiteboard",
            category="Presentation Equipment",
            quantity=2,
            is_available=True,
            notes="Whiteboards for meetings and seminars",
        ),
    ]

    db.add_all(resources)
    db.commit()

    print("Resources inserted successfully!")

    for resource in resources:
        print(
            resource.id,
            resource.name,
            resource.hall_id,
            resource.quantity,
        )

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()
