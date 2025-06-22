from pydantic import BaseModel
from datetime import datetime

class MeasurementBase(BaseModel):
    x: int
    y: int
    qr_code_id: int

class MeasurementOut(MeasurementBase):
    measurement_id: int
    tracking_time: datetime

    class Config:
        from_attributes = True
