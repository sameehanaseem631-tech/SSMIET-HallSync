
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, Hall
from app.routers.booking import get_current_user

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


@router.get("/events")
def get_calendar_events(
    start_date: date | None = Query(
        None, description="Optional start date (YYYY-MM-DD)"
    ),
    end_date: date | None = Query(
        None, description="Optional end date (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if start_date and end_date and end_date < start_date:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="End date must be on or after start date",
        )

    query = (
        db.query(Booking, Hall.name.label("hall_name"))
        .join(Hall, Booking.hall_id == Hall.id)
        .filter(Booking.status.in_(["pending", "approved", "confirmed"]))
    )

    if start_date:
        query = query.filter(Booking.event_date >= start_date)

    if end_date:
        query = query.filter(Booking.event_date <= end_date)

    # Faculty see their own events; admins see all events.
    if user.role != "admin":
        query = query.filter(Booking.user_id == user.id)

    results = query.order_by(
        Booking.event_date, Booking.start_time
    ).all()

    return [
        {
            "id": booking.id,
            "event_name": booking.event_name,
            "event_description": booking.event_description,
            "event_date": booking.event_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "hall_id": booking.hall_id,
            "hall_name": hall_name,
            "attendees": booking.attendees,
            "status": booking.status,
            "user_id": booking.user_id,
        }
        for booking, hall_name in results
    ]
