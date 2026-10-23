
from app.database import SessionLocal
from app.models import Hall

HALLS = [
    {
        "name": "Main Auditorium",
        "location": "Main Block",
        "capacity": 500,
        "facilities": "Projector, Sound System, Stage, AC",
        "description": "Large auditorium for college events",
    },
    {
        "name": "Seminar Hall A",
        "location": "Academic Block",
        "capacity": 150,
        "facilities": "Projector, Sound System, AC",
        "description": "Seminars and guest lectures",
    },
    {
        "name": "Seminar Hall B",
        "location": "Academic Block",
        "capacity": 100,
        "facilities": "Projector, Whiteboard",
        "description": "Meetings and department seminars",
    },
    {
        "name": "Conference Room",
        "location": "Administration Block",
        "capacity": 40,
        "facilities": "Display Screen, Conference Table, AC",
        "description": "Faculty meetings and discussions",
    },
]

db = SessionLocal()

try:
    added = 0

    for hall_data in HALLS:
        existing = db.query(Hall).filter(
            Hall.name == hall_data["name"]
        ).first()

        if existing:
            print(f"Already exists: {hall_data['name']}")
        else:
            db.add(Hall(**hall_data))
            added += 1

    db.commit()
    print(f"Finished! {added} hall(s) added.")

except Exception as error:
    db.rollback()
    print("Error:", error)

finally:
    db.close()
