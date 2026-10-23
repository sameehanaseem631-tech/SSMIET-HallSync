
from datetime import date, time
from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    hall_id: int = Field(gt=0)
    event_name: str = Field(min_length=3, max_length=200)
    event_description: str | None = None
    event_date: date
    start_time: time
    end_time: time
    attendees: int = Field(gt=0)


class BookingResponse(BaseModel):
    id: int
    user_id: int
    hall_id: int
    event_name: str
    event_description: str | None
    event_date: date
    start_time: time
    end_time: time
    attendees: int
    status: str
    admin_remarks: str | None = None

    model_config = ConfigDict(from_attributes=True)
