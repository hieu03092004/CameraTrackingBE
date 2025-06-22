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

   
    def qr_detection(self, frame_to_process: np.ndarray):
        """
        Phát hiện QR codes từ một frame được cung cấp.
        Hàm này không phụ thuộc vào trạng thái self.current_frame.

        Args:
            frame_to_process (np.ndarray): Frame ảnh cần xử lý.

        Returns:
            list: Một danh sách các dictionary chứa thông tin 'rect', 'name', và 'center' của các QR codes được phát hiện.
        """
        if frame_to_process is None:
            logger.error("Đã nhận frame rỗng để xử lý QR.")
            return []

        logger.info("Đã vào hàm qr_detection")
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

                # Tạo ROI rectangle
                rect = (x_min, y_min, x_max, y_max)
                name = text or f"QR_{len(self.rois)}"

                # Thêm thông tin đầy đủ vào danh sách
                # detection_info = {
                #     "rect": rect,
                #     "name": name,
                #     "center": (center_x, center_y)
                # }
                # new_rois.append(detection_info)
                new_rois.append((rect, name))
                print(f"center_x: {center_x}, center_y: {center_y}")
                # Theo dõi vị trí laser và QR
                if len(new_rois) + len(self.rois) >= 4:
                    combined_rois = self.rois + new_rois
                    self.laser_positions_original = np.array([
                        [round((r[1][0] + r[1][2]) / 2), round((r[1][1] + r[1][3]) / 2)]
                        for r in combined_rois[:3]
                    ])
                    self.qr_position_original = np.array([
                        round((combined_rois[3][1][0] + combined_rois[3][1][2]) / 2),
                        round((combined_rois[3][1][1] + combined_rois[3][1][3]) / 2)
                    ])

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
        
        return new_rois # <-- Trả về danh sách các dictionary

    def get_width_roi(self, x1,y1,x2,y2):
        width = {}
        try:
            width = abs(x2 - x1)
        except Exception as e:
            print(f"Error parsing rect at row {i}: {e}")
            # Thêm None hoặc giá trị mặc định nếu có lỗi
        return width

# Tạo instance global
rtsp_service = RTSPService() 