
from pydantic import BaseModel, ConfigDict, Field


class ResourceCreate(BaseModel):
    hall_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=50)
    quantity: int = Field(ge=1)
    notes: str | None = None


class ResourceUpdate(BaseModel):
    hall_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=2, max_length=100)
    category: str | None = Field(default=None, min_length=2, max_length=50)
    quantity: int | None = Field(default=None, ge=1)
    is_available: bool | None = None
    notes: str | None = None


class ResourceResponse(BaseModel):
    id: int
    hall_id: int
    name: str
    category: str
    quantity: int
    is_available: bool
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)
