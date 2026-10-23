
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Hall, Booking

router = APIRouter(prefix="/api/halls", tags=["Halls"])


def hall_to_dict(hall: Hall):
    return {
        "id": hall.id,
        "name": hall.name,
        "location": hall.location,
        "capacity": hall.capacity,
        "facilities": hall.facilities,
        "description": hall.description,
        "is_available": hall.is_available,
    }


@router.get("/")
def get_halls(db: Session = Depends(get_db)):
    halls = db.query(Hall).order_by(Hall.id).all()
    return [hall_to_dict(hall) for hall in halls]


@router.get("/availability")
def check_hall_availability(
    event_date: date = Query(..., description="Date in YYYY-MM-DD format"),
    start_time: time = Query(..., description="Start time, e.g. 09:00"),
    end_time: time = Query(..., description="End time, e.g. 10:30"),
    attendees: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    if end_time <= start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be later than start time",
        )

    halls = (
        db.query(Hall)
        .filter(
            Hall.is_available.is_(True),
            Hall.capacity >= attendees,
        )
        .order_by(Hall.id)
        .all()
    )

    available_halls = []

    for hall in halls:
        conflict = (
            db.query(Booking.id)
            .filter(
                Booking.hall_id == hall.id,
                Booking.event_date == event_date,
                Booking.status.in_(["pending", "approved", "confirmed"]),
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            )
            .first()
        )

        if not conflict:
            available_halls.append(hall_to_dict(hall))

    return {
        "event_date": event_date,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
        "available_count": len(available_halls),
        "available_halls": available_halls,
    }


@router.get("/{hall_id}")
def get_hall(hall_id: int, db: Session = Depends(get_db)):
    hall = db.query(Hall).filter(Hall.id == hall_id).first()

    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")

    return hall_to_dict(hall)
