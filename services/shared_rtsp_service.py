"""
Shared RTSP service để chia sẻ frame từ 1 camera cho nhiều threads
"""
import cv2
import threading
import time
import queue
from typing import Optional, Dict
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SharedRTSPService:
    """
    Service để chia sẻ frame từ một camera cho nhiều threads
    """
    
    def __init__(self):
        self._streams = {}  # Dictionary để lưu trữ các stream
        self._locks = {}    # Locks cho từng stream
        
    def get_shared_frame(self, rtsp_url: str, thread_id: str) -> Optional[np.ndarray]:
        """
        Lấy frame từ shared stream hoặc tạo mới nếu chưa có
        """
        if rtsp_url not in self._streams:
            # Tạo lock cho stream này
            self._locks[rtsp_url] = threading.Lock()
            
        # Sử dụng lock để đảm bảo chỉ có 1 thread truy cập camera tại một thời điểm
        with self._locks[rtsp_url]:
            logger.info(f"[{thread_id}] 🔒 Đã lock camera để lấy frame")
            
            cap = None
            try:
                start_time = time.time()
                logger.info(f"[{thread_id}] ⏰ Bắt đầu kết nối RTSP lúc: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
                
                cap = cv2.VideoCapture(rtsp_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if not cap.isOpened():
                    logger.error(f"[{thread_id}] ❌ Không thể mở RTSP stream")
                    return None
                
                # Đọc frame
                ret, frame = cap.read()
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                
                if ret and frame is not None:
                    logger.info(f"[{thread_id}] ✅ Lấy frame thành công trong {duration:.2f}ms")
                    logger.info(f"[{thread_id}] 🔓 Giải phóng lock camera")
                    return frame.copy()  # Trả về copy để tránh xung đột
                else:
                    logger.error(f"[{thread_id}] ❌ Không thể đọc frame")
                    return None
                    
            except Exception as e:
                logger.error(f"[{thread_id}] ❌ Lỗi khi lấy frame: {e}")
                return None
            finally:
                if cap is not None:
                    cap.release()

# Instance global
shared_rtsp_service = SharedRTSPService()
