from pydantic import BaseModel
from datetime import datetime

class QrCodeBase(BaseModel):
    name_roi: str
    initial_x: int
    initial_y: int

class QrCodeOut(QrCodeBase):
    qr_code_id: int
    initial_time: datetime

    class Config:
        from_attributes = True
