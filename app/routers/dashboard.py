
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, Hall, Maintenance, User
from app.routers.booking import get_current_user


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    is_admin = user.role == "admin"

    # Faculty sees their own bookings.
    # Admin sees all bookings.
    booking_query = db.query(Booking)

    if not is_admin:
        booking_query = booking_query.filter(
            Booking.user_id == user.id
        )

    total_bookings = booking_query.count()

    pending_bookings = booking_query.filter(
        Booking.status == "pending"
    ).count()

    approved_bookings = booking_query.filter(
        Booking.status.in_(["approved", "confirmed"])
    ).count()

    cancelled_bookings = booking_query.filter(
        Booking.status == "cancelled"
    ).count()

    # Hall statistics
    total_halls = db.query(Hall).count()

    available_halls = db.query(Hall).filter(
        Hall.is_available.is_(True)
    ).count()

    # Maintenance statistics
    maintenance_query = db.query(Maintenance)

    if not is_admin:
        maintenance_query = maintenance_query.filter(
            Maintenance.reported_by == user.id
        )

    open_maintenance = maintenance_query.filter(
        Maintenance.status == "open"
    ).count()

    in_progress_maintenance = maintenance_query.filter(
        Maintenance.status == "in_progress"
    ).count()

    completed_maintenance = maintenance_query.filter(
        Maintenance.status == "completed"
    ).count()

    return {
        "dashboard": "SSMIET HallSync AI",
        "user_role": user.role,
        "statistics": {
            "total_halls": total_halls,
            "halls_marked_available": available_halls,
            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "approved_bookings": approved_bookings,
            "cancelled_bookings": cancelled_bookings,
            "open_maintenance": open_maintenance,
            "in_progress_maintenance": in_progress_maintenance,
            "completed_maintenance": completed_maintenance,
        },
    }
