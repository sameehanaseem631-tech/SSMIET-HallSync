
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from app.database import get_db, settings
from app.models import Booking, Hall, User
from app.schemas.booking import BookingCreate, BookingResponse

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


@router.post("/", response_model=BookingResponse, status_code=201)
def create_booking(
    data: BookingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.event_date < date.today():
        raise HTTPException(status_code=400, detail="Event date cannot be in the past")

    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    hall = db.query(Hall).filter(Hall.id == data.hall_id).first()

    if hall is None or not hall.is_available:
        raise HTTPException(status_code=404, detail="Hall not found or unavailable")

    if data.attendees > hall.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Attendees exceed hall capacity ({hall.capacity})",
        )

    conflict = db.query(Booking).filter(
        Booking.hall_id == data.hall_id,
        Booking.event_date == data.event_date,
        Booking.status.in_(["pending", "approved", "confirmed"]),
        Booking.start_time < data.end_time,
        Booking.end_time > data.start_time,
    ).first()

    if conflict:
        raise HTTPException(
            status_code=409,
            detail="This hall already has a booking during that time",
        )

    booking = Booking(
        user_id=user.id,
        hall_id=data.hall_id,
        event_name=data.event_name,
        event_description=data.event_description,
        event_date=data.event_date,
        start_time=data.start_time,
        end_time=data.end_time,
        attendees=data.attendees,
        status="pending",
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking


@router.get("/my", response_model=list[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Booking)
        .filter(Booking.user_id == user.id)
        .order_by(Booking.id.desc())
        .all()
    )

@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="You can only cancel your own bookings",
        )

    if booking.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Booking is already cancelled",
        )

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)

    return booking


@router.patch("/{booking_id}/approve", response_model=BookingResponse)
def approve_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can approve bookings",
        )

    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending bookings can be approved",
        )

    booking.status = "approved"
    db.commit()
    db.refresh(booking)

    return booking
