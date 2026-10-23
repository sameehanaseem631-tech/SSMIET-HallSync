
from datetime import date, time

from pydantic import BaseModel, Field, model_validator


class HallRecommendationRequest(BaseModel):
    event_date: date
    start_time: time
    end_time: time
    attendees: int = Field(gt=0)
    required_facilities: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_event_time(self):
        if self.end_time <= self.start_time:
            raise ValueError("End time must be later than start time")
        return self
