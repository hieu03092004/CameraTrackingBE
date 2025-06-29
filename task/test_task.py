from apscheduler.schedulers.background import BackgroundScheduler
import logging
import sys
import os
from datetime import datetime, time, timedelta

# Thêm đường dẫn gốc của dự án vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rtsp_service import rtsp_service
from services.database_service import database_service
from db.database import get_connection

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CameraTaskServiceTest:
    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)

    def _check_and_process_cameras(self):
        """
        Công việc được lên lịch để kiểm tra thời gian và xử lý camera.
        Chỉ thực hiện khi thời gian hiện tại khớp với capture_time trong database.
        """
        current_time = datetime.now().time()
        logger.info(f"Kiểm tra thời gian hiện tại: {current_time.strftime('%H:%M:%S')}")
        
        # Lấy danh sách lịch chụp đang hoạt động
        active_schedules = database_service.get_active_schedules()
        
        if not active_schedules:
            logger.info("Không có lịch chụp nào đang hoạt động.")
            return
        
        logger.info(f"Tìm thấy {len(active_schedules)} lịch chụp đang hoạt động")
        
        # Kiểm tra xem thời gian hiện tại có khớp với bất kỳ capture_time nào không
        matching_schedules = []
        for schedule in active_schedules:
            capture_time_str = schedule['capture_time']
            # Chuyển đổi string thành time object
            if isinstance(capture_time_str, str):
                try:
                    capture_time = datetime.strptime(capture_time_str, '%H:%M:%S').time()
                except ValueError:
                    logger.warning(f"Không thể parse thời gian: {capture_time_str}")
                    continue
            else:
                capture_time = capture_time_str
            
            # So sánh thời gian (chỉ so sánh giờ và phút, bỏ qua giây)
            if (current_time.hour == capture_time.hour and 
                current_time.minute == capture_time.minute):
                matching_schedules.append(schedule)
                logger.info(f"✅ Thời gian khớp với lịch chụp: {capture_time_str}")
        
        if not matching_schedules:
            logger.info("Không có lịch chụp nào khớp với thời gian hiện tại.")
            return
        
        # Nếu có lịch chụp khớp, thực hiện xử lý camera
        logger.info(f"🚀 Bắt đầu xử lý camera theo {len(matching_schedules)} lịch chụp khớp")
        self._process_cameras()

    def _process_cameras(self):
        """
        Xử lý tất cả camera - lấy frame, phát hiện QR và lưu vào database.
        """
        logger.info("Bắt đầu tác vụ: Lấy danh sách camera từ Database.")
        
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                logger.error("Không thể kết nối đến database để lấy danh sách camera.")
                return

            with conn.cursor() as cursor:
                cursor.execute("SELECT name, rtsp_url, camera_id FROM cameras")
                cameras = cursor.fetchall()

            if not cameras:
                logger.warning("Không có camera nào được tìm thấy từ Database.")
                return

            logger.info(f"Tìm thấy {len(cameras)} camera. Bắt đầu xử lý...")

            for i, camera in enumerate(cameras):
                camera_name = camera.get('name', 'N/A')
                rtsp_url = camera.get('rtsp_url')
                camera_id = camera.get('camera_id', i)  # Lấy camera_id từ database hoặc dùng index

                if not rtsp_url:
                    logger.warning(f"Camera '{camera_name}' không có rtsp_url. Bỏ qua.")
                    continue

                logger.info(f"--- Đang xử lý Camera: {camera_name} (ID: {camera_id}) ---")
                logger.info(f"RTSP URL: {rtsp_url}")
                
                # 1. Lấy frame từ RTSP
                frame = rtsp_service.get_frame_from_rtsp(rtsp_url)

                if frame is not None:
                    # 2. Nếu lấy frame thành công, thực hiện nhận diện QR và lưu vào database
                    logger.info(f"Phát hiện QR cho Camera: {camera_name}")
                    newly_found_rois = rtsp_service.qr_detection_saveToDb_test(frame, camera_id)
                    
                    if newly_found_rois:
                        logger.info(f"Các ROI mới tìm thấy cho {camera_name}: {len(newly_found_rois)} QR codes")
                        # Log chi tiết từng QR code
                        for j, detection in enumerate(newly_found_rois):
                            rect, name, roi_width, center_x, center_y = detection
                            logger.info(f"  QR {j+1}: {name} - Center: ({center_x}, {center_y}) - Width: {roi_width}")
                        # Dữ liệu đã được tự động lưu vào database trong hàm qr_detection_saveToDb
                    else:
                        logger.info(f"Không tìm thấy ROI mới nào cho {camera_name}.")
                else:
                    logger.error(f"Không thể lấy frame cho Camera: {camera_name}")
                
                logger.info(f"--- Hoàn thành xử lý Camera: {camera_name} ---")

        except Exception as e:
            logger.error(f"Lỗi không xác định trong tác vụ: {e}")
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed.")

    def start(self):
        """
        Thêm công việc vào scheduler và bắt đầu chạy.
        Tính toán thời gian bắt đầu vào phút tiếp theo.
        Ví dụ: nếu start lúc 2:40:10 thì sẽ bắt đầu lúc 2:41:00 (realtime)
        """
        logger.info("Khởi động dịch vụ tác vụ nền...")
        
        # Tính toán thời gian bắt đầu vào phút tiếp theo (realtime)
        now = datetime.now()
        # Tính thời gian đến phút tiếp theo với giây = 0
        next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        logger.info(f"Thời gian hiện tại: {now.strftime('%H:%M:%S')}")
        logger.info(f"Sẽ bắt đầu kiểm tra lúc: {next_minute.strftime('%H:%M:%S')}")
        
        # Thêm job đầu tiên để chạy vào thời điểm đã tính toán
        self.scheduler.add_job(
            self._check_and_process_cameras,
            'date',
            run_date=next_minute,
            id='initial_camera_processing_job',
            replace_existing=True
        )
        
        # Thêm job định kỳ để chạy mỗi phút sau lần đầu tiên
        self.scheduler.add_job(
            self._check_and_process_cameras,
            'interval',
            minutes=1,
            id='periodic_camera_processing_job',
            replace_existing=True,
            start_date=next_minute + timedelta(minutes=1)  # Bắt đầu từ phút thứ 2
        )
        
        self.scheduler.start()
        logger.info("Dịch vụ tác vụ nền đã bắt đầu, sẽ kiểm tra mỗi phút từ thời điểm đã lên lịch.")

    def stop(self):
        """
        Dừng scheduler.
        """
        logger.info("Dừng dịch vụ tác vụ nền...")
        self.scheduler.shutdown()
        logger.info("Dịch vụ tác vụ nền đã dừng.")

# Tạo một instance để có thể import và sử dụng ở nơi khác
camera_task_service = CameraTaskServiceTest()
