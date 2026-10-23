
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Hall, Resource, User
from app.routers.booking import get_current_user
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
)

router = APIRouter(prefix="/api/resources", tags=["Resources"])


@router.get("/", response_model=list[ResourceResponse])
def get_resources(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Resource).order_by(Resource.id).all()


@router.post("/", response_model=ResourceResponse, status_code=201)
def create_resource(
    data: ResourceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can create resources",
        )

    hall = db.query(Hall).filter(Hall.id == data.hall_id).first()
    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")

    resource = Resource(
        hall_id=data.hall_id,
        name=data.name,
        category=data.category,
        quantity=data.quantity,
        notes=data.notes,
    )

    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.patch("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    data: ResourceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can update resources",
        )

    resource = (
        db.query(Resource)
        .filter(Resource.id == resource_id)
        .first()
    )

    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    updates = data.model_dump(exclude_unset=True)

    if "hall_id" in updates and updates["hall_id"] is not None:
        hall = db.query(Hall).filter(Hall.id == updates["hall_id"]).first()
        if hall is None:
            raise HTTPException(status_code=404, detail="Hall not found")

    for field, value in updates.items():
        setattr(resource, field, value)

    db.commit()
    db.refresh(resource)
    return resource
