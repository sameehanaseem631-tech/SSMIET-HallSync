
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Hall, Maintenance, User
from app.routers.booking import get_current_user
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
)

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance"])


@router.post("/", response_model=MaintenanceResponse, status_code=201)
def create_maintenance(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hall = db.query(Hall).filter(Hall.id == data.hall_id).first()
    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")

    if data.priority not in ["low", "medium", "high", "urgent"]:
        raise HTTPException(
            status_code=400,
            detail="Priority must be low, medium, high, or urgent",
        )

    item = Maintenance(
        hall_id=data.hall_id,
        reported_by=user.id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        status="open",
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can update maintenance requests",
        )

    item = (
        db.query(Maintenance)
        .filter(Maintenance.id == maintenance_id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    updates = data.model_dump(exclude_unset=True)

    if "status" in updates and updates["status"] not in [
        "open", "in_progress", "completed", "cancelled"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status",
        )

    if "priority" in updates and updates["priority"] not in [
        "low", "medium", "high", "urgent"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid priority",
        )

    for field, value in updates.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item
