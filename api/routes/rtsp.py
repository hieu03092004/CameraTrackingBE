from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import cv2
import base64
import numpy as np
from services.rtsp_service import rtsp_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class RTSPRequest(BaseModel):
    rtsp_url: str

class RTSPResponse(BaseModel):
    success: bool
    message: str
    frame_info: dict
    frame_base64: str = None

@router.post("/get-frame", response_model=RTSPResponse)
async def get_frame_from_rtsp(request: RTSPRequest):
    """
    Lấy frame từ RTSP stream
    
    Args:
        request: Chứa RTSP URL
        
    Returns:
        RTSPResponse: Thông tin frame và frame được encode base64
    """
    try:
        # Lấy frame từ RTSP stream
        frame = rtsp_service.get_frame_from_rtsp(request.rtsp_url)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Không thể lấy frame từ RTSP stream")
        
        # Lấy thông tin frame
        frame_info = rtsp_service.get_frame_info(frame)
        
        # Encode frame thành base64 để trả về
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        logger.info(f"Đã xử lý thành công frame từ: {request.rtsp_url}")
        
        return RTSPResponse(
            success=True,
            message="Lấy frame thành công",
            frame_info=frame_info,
            frame_base64=frame_base64
        )
        
    except Exception as e:
        logger.error(f"Lỗi khi xử lý RTSP request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")

@router.get("/test-rtsp")
async def test_rtsp():
    """
    Test endpoint với RTSP URL mặc định
    """
    test_url = "rtsp://admin:Imou0588!@192.168.1.103:554/cam/realmonitor?channel=1&subtype=0"
    
    try:
        frame = rtsp_service.get_frame_from_rtsp(test_url)
        
        if frame is None:
            return {"success": False, "message": "Không thể lấy frame từ test URL"}
        
        frame_info = rtsp_service.get_frame_info(frame)
        
        # Encode frame thành base64
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "success": True,
            "message": "Test thành công",
            "frame_info": frame_info,
            "frame_base64": frame_base64
        }
        
    except Exception as e:
        return {"success": False, "message": f"Lỗi test: {str(e)}"} 