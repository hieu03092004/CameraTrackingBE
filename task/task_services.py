from apscheduler.schedulers.background import BackgroundScheduler
import logging
import sys
import os

# Thêm đường dẫn gốc của dự án vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rtsp_service import rtsp_service
from db.database import get_connection

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CameraTaskService:
    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)

    def _fetch_and_process_cameras(self):
        """
        Công việc được lên lịch để lấy danh sách camera trực tiếp từ database.
        """
        logger.info("Bắt đầu tác vụ định kỳ: Lấy danh sách camera từ Database.")
        
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                logger.error("Không thể kết nối đến database để lấy danh sách camera.")
                return

            with conn.cursor() as cursor:
                cursor.execute("SELECT name, rtsp_url FROM cameras")
                cameras = cursor.fetchall()

            if not cameras:
                logger.warning("Không có camera nào (đang hoạt động) được tìm thấy từ Database.")
                return

            logger.info(f"Tìm thấy {len(cameras)} camera. Bắt đầu xử lý...")

            for camera in cameras:
                camera_name = camera.get('name', 'N/A')
                rtsp_url = camera.get('rtsp_url')

                if not rtsp_url:
                    logger.warning(f"Camera '{camera_name}' không có rtsp_url. Bỏ qua.")
                    continue

                logger.info(f"--- Đang xử lý Camera: {camera_name} ---")
                logger.info(f"RTSP URL: {rtsp_url}")
                
                # 1. Lấy frame từ RTSP
                frame = rtsp_service.get_frame_from_rtsp(rtsp_url)

                if frame is not None:
                    # 2. Nếu lấy frame thành công, thực hiện nhận diện QR
                    logger.info(f"Phát hiện QR cho Camera: {camera_name}")
                    newly_found_rois = rtsp_service.qr_detection(frame)
                    
                    if newly_found_rois:
                        logger.info(f"Các ROI mới tìm thấy cho {camera_name}: {newly_found_rois}")
                        # Tại đây bạn có thể làm gì đó với các ROI mới, ví dụ: lưu vào database
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
        """
        logger.info("Khởi động dịch vụ tác vụ nền...")
        self.scheduler.add_job(
            self._fetch_and_process_cameras,
            'interval',
            seconds=30,
            id='camera_processing_job',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Dịch vụ tác vụ nền đã bắt đầu, sẽ chạy mỗi 30 giây.")

    def stop(self):
        """
        Dừng scheduler.
        """
        logger.info("Dừng dịch vụ tác vụ nền...")
        self.scheduler.shutdown()
        logger.info("Dịch vụ tác vụ nền đã dừng.")

# Tạo một instance để có thể import và sử dụng ở nơi khác
camera_task_service = CameraTaskService()
