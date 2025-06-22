from pydantic import BaseModel
from datetime import time

class ScheduleTimeBase(BaseModel):
    capture_time: time
    is_active: bool = True

class ScheduleTimeOut(ScheduleTimeBase):
    schedule_time_id: int

    class Config:
        from_attributes = True
