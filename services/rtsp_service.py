import cv2,zxingcpp
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
    def detect_qr_and_print(self,frame):
    # Đọc barcode/QRCodes
        results = zxingcpp.read_barcodes(frame)
        for result in results:
            if result.format != zxingcpp.BarcodeFormat.QRCode or not result.position:
                continue

            # Lấy 4 điểm góc và quy về integer
            pts = [
                (round(result.position.top_left.x),   round(result.position.top_left.y)),
                (round(result.position.top_right.x),  round(result.position.top_right.y)),
                (round(result.position.bottom_right.x), round(result.position.bottom_right.y)),
                (round(result.position.bottom_left.x),  round(result.position.bottom_left.y))
            ]

            # Tính x_min, y_min, x_max, y_max
            x_coords = [p[0] for p in pts]
            y_coords = [p[1] for p in pts]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)

            # Tính tâm (center)
            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2

            # In ra kết quả
            print(f"QR Text: {result.text}")
            print(f"  Center: (x={center_x}, y={center_y})")
            print(f"  ROI rect: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
            print("-" * 40)
# Tạo instance global
rtsp_service = RTSPService() 