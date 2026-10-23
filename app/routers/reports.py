
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, Hall, User
from app.routers.booking import get_current_user


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


@router.get("/analytics")
def get_report_analytics(
    start_date: date | None = Query(
        default=None,
        description="Report start date (YYYY-MM-DD)",
    ),
    end_date: date | None = Query(
        default=None,
        description="Report end date (YYYY-MM-DD)",
    ),
    operating_hours_per_day: float = Query(
        default=8.0,
        gt=0,
        le=24,
        description="Assumed daily operating hours per hall",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Default period: current month through today.
    today = date.today()

    if end_date is None:
        end_date = today

    if start_date is None:
        start_date = end_date.replace(day=1)

    if start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be before or equal to end_date",
        )

    period_days = (end_date - start_date).days + 1

    # Admin sees all bookings; other users see their own.
    query = (
        db.query(Booking, Hall, User)
        .join(Hall, Booking.hall_id == Hall.id)
        .join(User, Booking.user_id == User.id)
        .filter(
            Booking.event_date >= start_date,
            Booking.event_date <= end_date,
        )
    )

    if current_user.role != "admin":
        query = query.filter(
            Booking.user_id == current_user.id
        )

    rows = query.order_by(
        Booking.event_date,
        Booking.start_time,
    ).all()

    halls = db.query(Hall).order_by(Hall.id).all()

    total_bookings = len(rows)
    cancelled_bookings = sum(
        1 for booking, hall, user in rows
        if booking.status == "cancelled"
    )

    cancellation_rate = (
        cancelled_bookings / total_bookings * 100
        if total_bookings
        else 0.0
    )

    # Booking trends: daily counts, including dates with zero bookings.
    daily_counts = Counter(
        booking.event_date
        for booking, hall, user in rows
    )

    trend_table = []
    current_day = start_date

    while current_day <= end_date:
        trend_table.append({
            "date": current_day.isoformat(),
            "bookings": daily_counts[current_day],
        })
        current_day += timedelta(days=1)

    # Status distribution: include statuses found in the data.
    status_counts = Counter(
        booking.status
        for booking, hall, user in rows
    )

    status_table = [
        {
            "status": status,
            "count": count,
            "percentage": round(
                count / total_bookings * 100, 2
            ) if total_bookings else 0.0,
        }
        for status, count in sorted(status_counts.items())
    ]

    # Calculate booked hours per hall.
    # Cancelled bookings do not consume utilization hours.
    booked_hours_by_hall = defaultdict(float)

    for booking, hall, user in rows:
        if booking.status == "cancelled":
            continue

        start_dt = datetime.combine(
            booking.event_date, booking.start_time
        )
        end_dt = datetime.combine(
            booking.event_date, booking.end_time
        )

        duration_hours = (
            end_dt - start_dt
        ).total_seconds() / 3600

        if duration_hours > 0:
            booked_hours_by_hall[hall.id] += duration_hours

    available_hours_per_hall = (
        period_days * operating_hours_per_day
    )

    hall_table = []

    for hall in halls:
        booked_hours = booked_hours_by_hall[hall.id]

        utilization = (
            booked_hours / available_hours_per_hall * 100
            if available_hours_per_hall
            else 0.0
        )

        hall_table.append({
            "hall_id": hall.id,
            "hall_name": hall.name,
            "booked_hours": round(booked_hours, 2),
            "available_hours": round(
                available_hours_per_hall, 2
            ),
            "utilization_percentage": round(
                utilization, 2
            ),
        })

    hall_table.sort(
        key=lambda item: item["utilization_percentage"],
        reverse=True,
    )

    average_utilization = (
        sum(
            item["utilization_percentage"]
            for item in hall_table
        ) / len(hall_table)
        if hall_table
        else 0.0
    )

    busiest_hall = (
        max(
            hall_table,
            key=lambda item: item["booked_hours"],
        )
        if hall_table
        else None
    )

    # Department counts.
    # If User.department has not been added yet, show Unassigned.
    department_counts = Counter()

    for booking, hall, booking_user in rows:
        department = (
            getattr(booking_user, "department", None)
            or "Unassigned"
        )
        department_counts[department] += 1

    department_table = [
        {
            "department": department,
            "bookings": count,
        }
        for department, count in sorted(
            department_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    return {
        "report_title": "SSMIET HallSync AI - Analytics Report",
        "generated_for_role": current_user.role,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days": period_days,
        },
        "kpis": {
            "total_bookings": total_bookings,
            "average_utilization_percentage": round(
                average_utilization, 2
            ),
            "cancellation_rate_percentage": round(
                cancellation_rate, 2
            ),
            "busiest_hall": (
                {
                    "hall_id": busiest_hall["hall_id"],
                    "hall_name": busiest_hall["hall_name"],
                    "booked_hours": busiest_hall["booked_hours"],
                }
                if busiest_hall
                and busiest_hall["booked_hours"] > 0
                else None
            ),
        },
        "chart_data": {
            # Use as a line chart.
            "booking_trends": trend_table,

            # Use as a horizontal bar chart.
            "hall_utilization": hall_table,

            # Use as a vertical bar chart.
            "bookings_by_department": department_table,

            # Use as a pie/doughnut chart.
            "booking_status": status_table,
        },
        "tables": {
            "booking_trends": trend_table,
            "hall_utilization": hall_table,
            "bookings_by_department": department_table,
            "booking_status": status_table,
        },
        "utilization_method": {
            "description": (
                "Booked non-cancelled hours divided by "
                "assumed available operating hours."
            ),
            "operating_hours_per_day": operating_hours_per_day,
        },
    }
