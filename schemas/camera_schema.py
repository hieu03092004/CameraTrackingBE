from pydantic import BaseModel

class CameraCreate(BaseModel):
    name: str
    rtsp_url: str
    input_size_value: float

class CameraOut(CameraCreate):
    camera_id: int

    class Config:
        from_attributes = True
