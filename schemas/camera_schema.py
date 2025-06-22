from pydantic import BaseModel
from typing import Optional

class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    conversion_rate: Optional[float] = None

class CameraOut(CameraCreate):
    camera_id: int

    class Config:
        from_attributes = True
