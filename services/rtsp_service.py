import cv2,zxingcpp
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging
import time
from services.database_service import database_service
# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTSPService:
    def __init__(self):
        self.cap = None
        self.current_frame = None
        self.rois = []
    
    def get_frame_from_rtsp(self, rtsp_url: str) -> Optional[np.ndarray]:
    
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
            self.current_frame = frame
           

            
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

   
    def qr_detection_saveToDb(self, frame_to_process: np.ndarray):
        """
        Phát hiện QR codes từ một frame được cung cấp và lưu vào database.
        - Nếu QR name chưa có trong bảng qr_codes: insert vào qr_codes
        - Nếu QR name đã có: insert vào bảng measurements

        Args:
            frame_to_process (np.ndarray): Frame ảnh cần xử lý.

        Returns:
            list: Một danh sách các tuple chứa thông tin (rect, name, roi_width, center_x, center_y) của các QR codes được phát hiện.
        """
        if frame_to_process is None:
            logger.error("Đã nhận frame rỗng để xử lý QR.")
            return []

        logger.info("Đã vào hàm qr_detection_saveToDb")
        frame_copy = frame_to_process.copy()

        # Sử dụng zxingcpp để đọc barcodes
        results = zxingcpp.read_barcodes(frame_copy)
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
                name = text or f"QR_{len(self.rois)}"

                # ==================== LOGIC LƯU VÀO DATABASE ====================
                print(f"\n🔍 Xử lý QR code: {name}")
                print(f"   - Center: ({center_x}, {center_y})")
                print(f"   - ROI: ({x_min}, {y_min}, {x_max}, {y_max})")
                
                # Kiểm tra xem QR name đã tồn tại trong database chưa
                qr_exists = self.check_roi_name_exists(name)
                
                if not qr_exists:
                    # QR name chưa tồn tại -> insert vào bảng qr_codes
                    print(f"   📝 QR name '{name}' chưa tồn tại -> Thêm vào bảng qr_codes")
                    qr_code = database_service.create_qr_code(
                        name_roi=name,
                        initial_x=center_x,
                        initial_y=center_y
                    )
                    
                    if qr_code:
                        print(f"   ✅ Đã thêm QR code vào database: ID {qr_code['qr_code_id']}")
                    else:
                        print(f"   ❌ Không thể thêm QR code vào database")
                else:
                    # QR name đã tồn tại -> insert vào bảng measurements
                    print(f"   📊 QR name '{name}' đã tồn tại -> Thêm vào bảng measurements")
                    
                    # Lấy QR code ID từ database
                    qr_code = database_service.get_qr_code_by_name(name)
                    if qr_code:
                        measurement = database_service.create_measurement(
                            x=center_x,
                            y=center_y,
                            qr_code_id=qr_code['qr_code_id']
                        )
                        
                        if measurement:
                            print(f"   ✅ Đã thêm measurement vào database: ID {measurement['measurement_id']}")
                        else:
                            print(f"   ❌ Không thể thêm measurement vào database")
                    else:
                        print(f"   ❌ Không thể lấy QR code ID từ database")
                
                # ==================== KẾT THÚC LOGIC DATABASE ====================

                # Thêm thông tin đầy đủ vào danh sách với roi_width và center coordinates
                new_rois.append((rect, name, roi_width, center_x, center_y))
                print(f"center_x: {center_x}, center_y: {center_y}")
                
                # Theo dõi vị trí laser và QR
              

                # In ra thông tin QR code
                print(f"QR Text: {text}")
                print(f"  Center: (x={center_x}, y={center_y})")
                print(f"  ROI rect: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
                print(f"  Name: {name}")
                print("-" * 40)

        # Thêm các ROI mới vào danh sách chính
        # self.rois.extend(new_rois) # <-- Bỏ dòng này
        print("New rois found: ", new_rois)
        
        print(f"Tổng số QR codes phát hiện trong lần chạy này: {len(detected_qr_codes)}")
        
        return new_rois # <-- Trả về danh sách các tuple (rect, name, roi_width, center_x, center_y)

        
    def process_unit_conversion(self, rtsp_url: str, input_size_value: float):
        """
        Lấy frame từ RTSP, phát hiện QR codes và tính toán hệ số chuyển đổi.
        
        Args:
            rtsp_url (str): URL của RTSP stream
            input_size_value (float): Kích thước thực tế của QR code (mm)
            target_unit (str): Đơn vị đích (mặc định "mm")
        """
        print(f"🔄 Đang xử lý chuyển đổi đơn vị...")
        print(f"RTSP URL: {rtsp_url}")
        print(f"Input size value: {input_size_value} mm")
        
        # 1. Lấy frame từ RTSP
        frame = self.get_frame_from_rtsp(rtsp_url)
        if frame is None:
            print("❌ Không thể lấy frame từ RTSP stream")
            return None
        
        # 2. Phát hiện QR codes
        detections = self.qr_detection_saveToDb(frame)
        if not detections:
            print("Không phát hiện được QR code nào")
            return None
        
        # 3. Lấy roi_width đầu tiên (tất cả QR codes có cùng kích thước)
        first_detection = detections[0]
        rect, name, roi_width, center_x, center_y = first_detection
        
        print(f"✅ Phát hiện {len(detections)} QR codes")
        print(f"📏 Sử dụng roi_width đầu tiên: {roi_width} pixels")
        print(f"📐 Kích thước thực tế: {input_size_value} mm")
        
        # 4. Tính toán hệ số chuyển đổi
        if roi_width <= 0:
            print("❌ roi_width phải lớn hơn 0")
            return None
        
        if input_size_value <= 0:
            print("input_size_value phải lớn hơn 0")
            return None
        
        # Tính hệ số chuyển đổi: mm / pixel
        scale_factor = input_size_value / roi_width
        
        return scale_factor;

    def check_roi_name_exists(self, roi_name: str) -> bool:
        """
        Kiểm tra xem roi_name đã tồn tại trong bảng qr_codes chưa.
        
        Args:
            roi_name (str): Tên ROI cần kiểm tra
            
        Returns:
            bool: True nếu roi_name đã tồn tại, False nếu chưa
        """
        try:
            # Kiểm tra kết nối database
            if not database_service.connection:
                print("❌ Không thể kết nối database")
                return False
            
            # Lấy QR code theo tên
            qr_code = database_service.get_qr_code_by_name(roi_name)
            
            if qr_code:
              
                return True
            else:
                print(f"❌ ROI name '{roi_name}' chưa tồn tại trong database")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi khi kiểm tra ROI name: {e}")
            return False

# Tạo instance global
rtsp_service = RTSPService() 