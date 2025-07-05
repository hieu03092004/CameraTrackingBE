"""
Thread-safe RTSP service for concurrent camera processing
"""
import cv2
import zxingcpp
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging
import time
import threading
import os
from datetime import datetime
from services.thread_safe_db_service import thread_safe_db_service

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreadSafeRTSPService:
    """
    Thread-safe RTSP service không sử dụng instance variables để tránh xung đột
    """
    
    def __init__(self):
        # Tạo thư mục lưu frame nếu chưa có
        self.output_dir = "captured_frames"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def get_frame_from_rtsp(self, rtsp_url: str) -> Optional[np.ndarray]:
        """
        Thread-safe method to get frame from RTSP URL
        """
        cap = None
        thread_id = threading.current_thread().name
        
        # Thời gian bắt đầu kết nối RTSP
        rtsp_start_time = time.time()
        start_dt = datetime.fromtimestamp(rtsp_start_time)
        logger.info(f"[{thread_id}] ⏰ Bắt đầu kết nối RTSP lúc: {start_dt.strftime('%H:%M:%S')}.{start_dt.microsecond//1000:03d}ms")
        
        try:
            # Tạo VideoCapture object
            cap = cv2.VideoCapture(rtsp_url)
            
            # Thiết lập timeout cho RTSP
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Kiểm tra xem stream có được mở thành công không
            if not cap.isOpened():
                rtsp_end_time = time.time()
                rtsp_duration = (rtsp_end_time - rtsp_start_time) * 1000  # Convert to milliseconds
                logger.error(f"[{thread_id}] ❌ Không thể mở RTSP stream: {rtsp_url}")
                logger.error(f"[{thread_id}] ⏰ Thời gian kết nối thất bại: {rtsp_duration:.2f}ms")
                return None
            
            # Thời gian kết nối RTSP thành công
            rtsp_connected_time = time.time()
            rtsp_connect_duration = (rtsp_connected_time - rtsp_start_time) * 1000
            logger.info(f"[{thread_id}] ✅ Kết nối RTSP thành công sau: {rtsp_connect_duration:.2f}ms")
            
            # Thời gian bắt đầu đọc frame
            frame_start_time = time.time()
            frame_dt = datetime.fromtimestamp(frame_start_time)
            logger.info(f"[{thread_id}] 📸 Bắt đầu chụp frame lúc: {frame_dt.strftime('%H:%M:%S')}.{frame_dt.microsecond//1000:03d}ms")
            
            # Đọc frame với timeout
            ret, frame = cap.read()
            
            # Thời gian hoàn thành đọc frame
            frame_end_time = time.time()
            frame_duration = (frame_end_time - frame_start_time) * 1000
            
            if not ret or frame is None:
                logger.error(f"[{thread_id}] ❌ Không thể đọc frame từ RTSP stream")
                logger.error(f"[{thread_id}] ⏰ Thời gian đọc frame thất bại: {frame_duration:.2f}ms")
                return None
            
            logger.info(f"[{thread_id}] ✅ Đọc frame thành công sau: {frame_duration:.2f}ms")
            
            # Chuyển đổi frame sang BGR nếu cần (đảm bảo format nhất quán)
            if len(frame.shape) == 2:
                # Nếu là grayscale, chuyển sang BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                # Nếu là RGBA, chuyển sang BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            
            # Log thông tin frame và thời gian tổng
            height, width = frame.shape[:2]
            total_duration = (frame_end_time - rtsp_start_time) * 1000
            end_dt = datetime.fromtimestamp(frame_end_time)
            
            logger.info(f"[{thread_id}] 📊 Thông tin frame: {width}x{height}, Channels: {frame.shape[2] if len(frame.shape) > 2 else 1}")
            logger.info(f"[{thread_id}] ⏰ Tổng thời gian RTSP + Frame: {total_duration:.2f}ms")
            logger.info(f"[{thread_id}] ⏰ Hoàn thành lấy frame lúc: {end_dt.strftime('%H:%M:%S')}.{end_dt.microsecond//1000:03d}ms")
            
            return frame
            
        except Exception as e:
            error_time = time.time()
            error_duration = (error_time - rtsp_start_time) * 1000
            logger.error(f"[{thread_id}] ❌ Lỗi khi lấy frame từ RTSP: {str(e)}")
            logger.error(f"[{thread_id}] ⏰ Thời gian xử lý lỗi: {error_duration:.2f}ms")
            return None
        finally:
            # Đóng stream sau khi đọc frame
            if cap is not None:
                cap.release()
                cleanup_time = time.time()
                cleanup_dt = datetime.fromtimestamp(cleanup_time)
                logger.info(f"[{thread_id}] 🧹 Đóng RTSP connection lúc: {cleanup_dt.strftime('%H:%M:%S')}.{cleanup_dt.microsecond//1000:03d}ms")
    
    def qr_detection_saveToDb_safe(self, frame_to_process: np.ndarray, camera_id: int):
        """
        Thread-safe QR detection and database saving
        """
        if frame_to_process is None:
            logger.error("Đã nhận frame rỗng để xử lý QR.")
            return []

        thread_id = threading.current_thread().name
        
        # Thời gian bắt đầu QR detection
        qr_start_time = time.time()
        qr_dt = datetime.fromtimestamp(qr_start_time)
        logger.info(f"[{thread_id}] 🔍 Bắt đầu QR detection lúc: {qr_dt.strftime('%H:%M:%S')}.{qr_dt.microsecond//1000:03d}ms")
        logger.info(f"[{thread_id}] 📝 Đã vào hàm qr_detection_saveToDb_safe với camera_id: {camera_id}")
        
        frame_copy = frame_to_process.copy()

        # Thời gian bắt đầu đọc barcodes
        barcode_start_time = time.time()
        barcode_dt = datetime.fromtimestamp(barcode_start_time)
        logger.info(f"[{thread_id}] 🔍 Bắt đầu đọc barcodes lúc: {barcode_dt.strftime('%H:%M:%S')}.{barcode_dt.microsecond//1000:03d}ms")
        
        # Sử dụng zxingcpp để đọc barcodes
        results = zxingcpp.read_barcodes(frame_copy)
        
        # Thời gian hoàn thành đọc barcodes
        barcode_end_time = time.time()
        barcode_duration = (barcode_end_time - barcode_start_time) * 1000
        logger.info(f"[{thread_id}] ✅ Đọc barcodes hoàn thành sau: {barcode_duration:.2f}ms")
        logger.info(f"[{thread_id}] 📊 Tìm thấy {len(results)} barcode(s)")
        
        qr_codes = []

        for result in results:
            if result.format != zxingcpp.BarcodeFormat.QRCode or not result.position:
                continue

            # Convert position to points with rounding
            pts = [
                (round(result.position.top_left.x), round(result.position.top_left.y)),
                (round(result.position.top_right.x), round(result.position.top_right.y)),
                (round(result.position.bottom_right.x), round(result.position.bottom_right.y)),
                (round(result.position.bottom_left.x), round(result.position.bottom_left.y))
            ]

            qr_codes.append((result.text, pts))

        # Thời gian bắt đầu xử lý database
        db_start_time = time.time()
        db_dt = datetime.fromtimestamp(db_start_time)
        logger.info(f"[{thread_id}] 💾 Bắt đầu xử lý database lúc: {db_dt.strftime('%H:%M:%S')}.{db_dt.microsecond//1000:03d}ms")
        
        # Mảng để lưu QR codes đã được phát hiện (tránh trùng lặp)
        detected_qr_codes = []
        new_rois = []

        # Xử lý từng QR code được phát hiện
        for text, points in qr_codes:
            pts = np.array(points, dtype=np.int32)

            # Tính toán điểm trung tâm
            center_x = round(sum(pt[0] for pt in points) / 4)
            center_y = round(sum(pt[1] for pt in points) / 4)

            # Kiểm tra trùng lặp với ngưỡng 100px
            is_duplicate = any(
                abs(center_x - cx) < 100 and abs(center_y - cy) < 100
                for cx, cy in detected_qr_codes
            )

            if not is_duplicate:
                # Thêm vào danh sách QR đã phát hiện
                detected_qr_codes.append((center_x, center_y))

                # Tính toán tọa độ ROI với làm tròn
                x_min = round(min(pt[0] for pt in points))
                y_min = round(min(pt[1] for pt in points))
                x_max = round(max(pt[0] for pt in points))
                y_max = round(max(pt[1] for pt in points))

                # Đảm bảo kích thước chẵn cho ROI
                width = x_max - x_min
                height = y_max - y_min
                if width % 2 != 0:
                    x_max += 1
                if height % 2 != 0:
                    y_max += 1

                # Tính toán roi_width
                roi_width = abs(x_max - x_min)

                # Tạo ROI rectangle
                rect = (x_min, y_min, x_max, y_max)
                name = text or f"QR_Camera_{camera_id}_{len(detected_qr_codes)}"

                # ==================== LOGIC LƯU VÀO DATABASE ====================
                db_operation_start = time.time()
                db_op_dt = datetime.fromtimestamp(db_operation_start)
                print(f"\n[{thread_id}] 🔍 Xử lý QR code: {name} (Camera ID: {camera_id})")
                print(f"[{thread_id}]    - Center: ({center_x}, {center_y})")
                print(f"[{thread_id}]    - ROI: ({x_min}, {y_min}, {x_max}, {y_max})")
                print(f"[{thread_id}]    - Bắt đầu DB operation lúc: {db_op_dt.strftime('%H:%M:%S')}.{db_op_dt.microsecond//1000:03d}ms")
                
                # Kiểm tra xem QR name đã tồn tại trong database chưa
                # Sử dụng name của QR code để kiểm tra, không phải camera_id
                qr_exists = thread_safe_db_service.check_qr_name_exists_safe(name)
                print(f"[{thread_id}] QR '{name}' exists: {qr_exists}")
                
                if not qr_exists:
                    # QR name chưa tồn tại -> insert vào bảng qr_codes
                    print(f"[{thread_id}]    📝 QR name '{name}' chưa tồn tại -> Thêm vào bảng qr_codes")
                    qr_code = thread_safe_db_service.create_qr_code_safe(
                        name_roi=name,
                        initial_x=center_x,
                        initial_y=center_y
                    )
                    
                    if qr_code:
                        print(f"[{thread_id}]    ✅ Đã thêm QR code vào database: ID {qr_code['qr_code_id']}")
                    else:
                        print(f"[{thread_id}]    ❌ Không thể thêm QR code vào database")
                else:
                    # QR name đã tồn tại -> insert vào bảng measurements
                    print(f"[{thread_id}]    📊 QR name '{name}' đã tồn tại -> Thêm vào bảng measurements")
                    
                    # Lấy QR code ID từ database bằng name
                    qr_code = thread_safe_db_service.get_qr_code_by_name_safe(name)
                    if qr_code:
                        measurement = thread_safe_db_service.create_measurement_safe(
                            x=center_x,
                            y=center_y,
                            qr_code_id=qr_code['qr_code_id']
                        )
                        
                        if measurement:
                            print(f"[{thread_id}]    ✅ Đã thêm measurement vào database: ID {measurement['measurement_id']}")
                        else:
                            print(f"[{thread_id}]    ❌ Không thể thêm measurement vào database")
                    else:
                        print(f"[{thread_id}]    ❌ Không thể lấy QR code ID từ database")
                
                db_operation_end = time.time()
                db_operation_duration = (db_operation_end - db_operation_start) * 1000
                print(f"[{thread_id}]    ⏰ DB operation hoàn thành sau: {db_operation_duration:.2f}ms")
                
                # ==================== KẾT THÚC LOGIC DATABASE ====================

                # Thêm thông tin đầy đủ vào danh sách với roi_width và center coordinates
                new_rois.append((rect, name, roi_width, center_x, center_y))
                print(f"[{thread_id}] center_x: {center_x}, center_y: {center_y}")
                
                # In ra thông tin QR code
                print(f"[{thread_id}] QR Text: {text}")
                print(f"[{thread_id}]   Center: (x={center_x}, y={center_y})")
                print(f"[{thread_id}]   ROI rect: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
                print(f"[{thread_id}]   Name: {name}")
                print(f"[{thread_id}]" + "-" * 40)

        # Thời gian kết thúc toàn bộ QR detection
        qr_end_time = time.time()
        qr_end_dt = datetime.fromtimestamp(qr_end_time)
        
        # Tính toán thời gian các phần
        total_qr_duration = (qr_end_time - qr_start_time) * 1000
        
        print(f"[{thread_id}] New rois found: ", new_rois)
        print(f"[{thread_id}] Tổng số QR codes phát hiện trong lần chạy này: {len(detected_qr_codes)}")
        
        # Lưu frame với ROI nếu có QR codes được phát hiện
        if new_rois:
            saved_file = self.save_frame_with_roi(frame_to_process, new_rois, camera_id, thread_id)
            if saved_file:
                logger.info(f"[{thread_id}] 📸 Frame với ROI đã được lưu: {saved_file}")
        
        logger.info(f"[{thread_id}] ⏰ Tổng thời gian QR detection: {total_qr_duration:.2f}ms")
        logger.info(f"[{thread_id}] ⏰ Kết thúc QR detection lúc: {qr_end_dt.strftime('%H:%M:%S')}.{qr_end_dt.microsecond//1000:03d}ms")
        
        return new_rois

    def save_frame_with_roi(self, frame: np.ndarray, rois: list, camera_id: int, thread_id: str):
        """
        Lưu frame với ROI và center points được vẽ lên
        """
        if frame is None or not rois:
            return None
        
        # Tạo bản copy để vẽ
        frame_with_roi = frame.copy()
        
        # Màu sắc cho vẽ
        roi_color = (0, 255, 0)  # Xanh lá cho ROI
        center_color = (0, 0, 255)  # Đỏ cho center point
        text_color = (255, 255, 255)  # Trắng cho text
        
        for i, roi_info in enumerate(rois):
            rect, name, roi_width, center_x, center_y = roi_info
            x_min, y_min, x_max, y_max = rect
            
            # 1. Vẽ ROI rectangle
            cv2.rectangle(frame_with_roi, (x_min, y_min), (x_max, y_max), roi_color, 3)
            
            # 2. Vẽ center point
            cv2.circle(frame_with_roi, (center_x, center_y), 8, center_color, -1)
            cv2.circle(frame_with_roi, (center_x, center_y), 12, center_color, 2)
            
            # 3. Vẽ text thông tin
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2
            
            # Text QR name
            text = f"QR: {name}"
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            cv2.rectangle(frame_with_roi, (x_min, y_min - 30), 
                         (x_min + text_size[0] + 10, y_min), roi_color, -1)
            cv2.putText(frame_with_roi, text, (x_min + 5, y_min - 10), 
                       font, font_scale, text_color, thickness)
            
            # Text tọa độ center
            coord_text = f"Center: ({center_x}, {center_y})"
            cv2.putText(frame_with_roi, coord_text, (x_min, y_max + 25), 
                       font, 0.5, text_color, 1)
            
            # Text kích thước ROI
            size_text = f"Size: {roi_width}x{y_max-y_min}"
            cv2.putText(frame_with_roi, size_text, (x_min, y_max + 45), 
                       font, 0.5, text_color, 1)
        
        # Thêm thông tin tổng quan
        info_text = f"Camera {camera_id} - {thread_id} - QRs: {len(rois)}"
        cv2.putText(frame_with_roi, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
        # Thêm timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        cv2.putText(frame_with_roi, timestamp, (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        
        # Lưu file
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f"{self.output_dir}/camera_{camera_id}_{thread_id}_{timestamp_file}.jpg"
        
        success = cv2.imwrite(filename, frame_with_roi, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        if success:
            logger.info(f"[{thread_id}] 💾 Đã lưu frame với ROI: {filename}")
            return filename
        else:
            logger.error(f"[{thread_id}] ❌ Không thể lưu frame: {filename}")
            return None
    
    def save_frame_for_debug(self, frame: np.ndarray, camera_id: int, thread_id: str, qr_codes: list = None):
        """
        Lưu frame cho mục đích debug, có thể có hoặc không có QR codes
        """
        if frame is None:
            return None
        
        # Tạo bản copy để vẽ
        frame_debug = frame.copy()
        
        # Thêm thông tin camera và thread
        font = cv2.FONT_HERSHEY_SIMPLEX
        info_text = f"Camera {camera_id} - {thread_id}"
        cv2.putText(frame_debug, info_text, (10, 30), font, 0.8, (255, 255, 0), 2)
        
        # Thêm timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        cv2.putText(frame_debug, timestamp, (10, frame.shape[0] - 20), 
                   font, 0.6, (255, 255, 0), 1)
        
        # Nếu có QR codes, vẽ chúng
        if qr_codes:
            frame_debug = self._draw_qr_codes_on_frame(frame_debug, qr_codes)
            status_text = f"QR Codes: {len(qr_codes)} detected"
            cv2.putText(frame_debug, status_text, (10, 60), font, 0.6, (0, 255, 0), 2)
        else:
            status_text = "No QR Codes detected"
            cv2.putText(frame_debug, status_text, (10, 60), font, 0.6, (0, 255, 255), 2)
        
        # Lưu file
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f"{self.output_dir}/debug_camera_{camera_id}_{thread_id}_{timestamp_file}.jpg"
        
        success = cv2.imwrite(filename, frame_debug, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        if success:
            logger.info(f"[{thread_id}] 💾 Đã lưu debug frame: {filename}")
            return filename
        else:
            logger.error(f"[{thread_id}] ❌ Không thể lưu debug frame: {filename}")
            return None
    
    def _draw_qr_codes_on_frame(self, frame: np.ndarray, qr_codes: list):
        """
        Vẽ QR codes lên frame (helper method)
        """
        # Màu sắc cho vẽ
        roi_color = (0, 255, 0)  # Xanh lá cho ROI
        center_color = (0, 0, 255)  # Đỏ cho center point
        text_color = (255, 255, 255)  # Trắng cho text
        
        for i, qr_info in enumerate(qr_codes):
            rect, name, roi_width, center_x, center_y = qr_info
            x_min, y_min, x_max, y_max = rect
            
            # 1. Vẽ ROI rectangle
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), roi_color, 3)
            
            # 2. Vẽ center point
            cv2.circle(frame, (center_x, center_y), 8, center_color, -1)
            cv2.circle(frame, (center_x, center_y), 12, center_color, 2)
            
            # 3. Vẽ text thông tin
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            
            # Text QR name
            text = f"QR: {name}"
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            cv2.rectangle(frame, (x_min, y_min - 30), 
                         (x_min + text_size[0] + 10, y_min), roi_color, -1)
            cv2.putText(frame, text, (x_min + 5, y_min - 10), 
                       font, font_scale, text_color, thickness)
            
            # Text tọa độ center
            coord_text = f"({center_x}, {center_y})"
            cv2.putText(frame, coord_text, (x_min, y_max + 20), 
                       font, 0.5, text_color, 1)
        
        return frame

# Tạo instance global
thread_safe_rtsp_service = ThreadSafeRTSPService()
