import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging
import time

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTSPService:
    def __init__(self):
        self.cap = None
        self.current_frame = None
    
    def get_frame_from_rtsp(self, rtsp_url: str) -> Optional[np.ndarray]:
        """
        Lấy frame từ RTSP stream
        
        Args:
            rtsp_url (str): URL RTSP của camera
            
        Returns:
            Optional[np.ndarray]: Frame từ camera dưới dạng mảng số (numpy array) hoặc None nếu lỗi
        """
        try:
            # Tạo VideoCapture object
            self.cap = cv2.VideoCapture(rtsp_url)
            
            # Thiết lập timeout cho RTSP
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Kiểm tra xem stream có được mở thành công không
            if not self.cap.isOpened():
                logger.error(f"Không thể mở RTSP stream: {rtsp_url}")
                return None
            
            # Đọc frame với timeout
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                logger.error("Không thể đọc frame từ RTSP stream")
                return None
            
            # Chuyển đổi frame sang BGR nếu cần (đảm bảo format nhất quán)
            if len(frame.shape) == 2:
                # Nếu là grayscale, chuyển sang BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                # Nếu là RGBA, chuyển sang BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            
            # Cập nhật thông tin frame hiện tại
           

            
            # Log thông tin frame
            height, width = frame.shape[:2]
            logger.info(f"✅ Đã lấy frame thành công từ: {rtsp_url}")
            logger.info(f"📊 Thông tin frame: {width}x{height}, Channels: {frame.shape[2] if len(frame.shape) > 2 else 1}")
            
            return frame
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy frame từ RTSP: {str(e)}")
            return None
        finally:
            # Đóng stream sau khi đọc frame
            if self.cap is not None:
                self.cap.release()
                self.cap = None
    
  
    
   

        """
        Lấy thống kê về frame
        
        Returns:
            Dict[str, Any]: Thống kê frame
        """
        if self.current_frame is None:
            return {"error": "Không có frame nào"}
        
        frame = self.current_frame
        
        # Tính toán thống kê
        mean_values = np.mean(frame, axis=(0, 1))
        std_values = np.std(frame, axis=(0, 1))
        min_values = np.min(frame, axis=(0, 1))
        max_values = np.max(frame, axis=(0, 1))
        
        return {
            "mean": mean_values.tolist(),
            "std": std_values.tolist(),
            "min": min_values.tolist(),
            "max": max_values.tolist(),
            "timestamp": self.frame_timestamp,
            "frame_count": self.frame_count
        }

# Tạo instance global
rtsp_service = RTSPService() 