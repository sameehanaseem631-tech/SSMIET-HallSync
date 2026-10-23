
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Hall, User
from app.routers.booking import get_current_user


router = APIRouter(
    prefix="/api/campus-map",
    tags=["Campus Map"],
)


@router.get("/locations")
def get_campus_locations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    halls = (
        db.query(Hall)
        .order_by(Hall.id)
        .all()
    )

    locations = []

    for hall in halls:
        locations.append({
            "hall_id": hall.id,
            "name": hall.name,
            "location": hall.location,
            "capacity": hall.capacity,
            "facilities": hall.facilities or "",
            "description": hall.description or "",
            "is_available": hall.is_available,
        })

    return {
        "campus": "SSMIET",
        "total_locations": len(locations),
        "locations": locations,
    }


@router.get("/locations/{hall_id}")
def get_campus_location(
    hall_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hall = db.query(Hall).filter(
        Hall.id == hall_id
    ).first()

    if hall is None:
        raise HTTPException(
            status_code=404,
            detail="Hall location not found",
        )

    return {
        "hall_id": hall.id,
        "name": hall.name,
        "location": hall.location,
        "capacity": hall.capacity,
        "facilities": hall.facilities or "",
        "description": hall.description or "",
        "is_available": hall.is_available,
    }
