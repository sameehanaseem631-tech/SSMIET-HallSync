
from app.database import SessionLocal
from app.models import Maintenance

db = SessionLocal()

try:
    requests = [
        Maintenance(
            hall_id=1,
            reported_by=1,
            title="Projector not working",
            description="The projector is not displaying images properly.",
            priority="high",
            status="open",
        ),
        Maintenance(
            hall_id=2,
            reported_by=1,
            title="Air conditioning issue",
            description="The air conditioner needs inspection.",
            priority="medium",
            status="open",
        ),
        Maintenance(
            hall_id=3,
            reported_by=1,
            title="Whiteboard replacement",
            description="The whiteboard surface needs replacement.",
            priority="low",
            status="open",
        ),
    ]

    db.add_all(requests)
    db.commit()

    print("Maintenance requests inserted successfully!")

    for request in requests:
        print(request.id, request.title, request.priority, request.status)

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()
