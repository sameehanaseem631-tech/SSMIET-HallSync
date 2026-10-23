
from pydantic import BaseModel, ConfigDict, Field


class MaintenanceCreate(BaseModel):
    hall_id: int = Field(gt=0)
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=5)
    priority: str = "medium"


class MaintenanceUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    admin_remarks: str | None = None


class MaintenanceResponse(BaseModel):
    id: int
    hall_id: int
    reported_by: int
    title: str
    description: str
    priority: str
    status: str
    admin_remarks: str | None
    model_config = ConfigDict(from_attributes=True)
