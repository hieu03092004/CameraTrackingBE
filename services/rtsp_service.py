import cv2
import numpy as np
from typing import Optional, Tuple
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTSPService:
    def __init__(self):
        self.cap = None
    
    def get_frame_from_rtsp(self, rtsp_url: str) -> Optional[np.ndarray]:
        """
        Lấy frame từ RTSP stream
        
        Args:
            rtsp_url (str): URL RTSP của camera
            
        Returns:
            Optional[np.ndarray]: Frame từ camera hoặc None nếu lỗi
        """
        try:
            # Tạo VideoCapture object
            self.cap = cv2.VideoCapture(rtsp_url)
            
            # Kiểm tra xem stream có được mở thành công không
            if not self.cap.isOpened():
                logger.error(f"Không thể mở RTSP stream: {rtsp_url}")
                return None
            
            # Đọc frame
            ret, frame = self.cap.read()
            
            if not ret:
                logger.error("Không thể đọc frame từ RTSP stream")
                return None
            
            logger.info(f"Đã lấy frame thành công từ: {rtsp_url}")
            logger.info(f"Kích thước frame: {frame.shape}")
            
            return frame
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy frame từ RTSP: {str(e)}")
            return None
        finally:
            # Đóng stream sau khi đọc frame
            if self.cap is not None:
                self.cap.release()
    
    def get_frame_info(self, frame: np.ndarray) -> dict:
        """
        Lấy thông tin về frame
        
        Args:
            frame (np.ndarray): Frame từ camera
            
        Returns:
            dict: Thông tin về frame
        """
        if frame is None:
            return {"error": "Frame không hợp lệ"}
        
        return {
            "shape": frame.shape,
            "dtype": str(frame.dtype),
            "size_bytes": frame.nbytes,
            "channels": frame.shape[2] if len(frame.shape) > 2 else 1
        }

# Tạo instance global
rtsp_service = RTSPService() 