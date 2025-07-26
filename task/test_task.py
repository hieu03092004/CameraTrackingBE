from apscheduler.schedulers.background import BackgroundScheduler
import logging
import sys
import os
import time
from datetime import datetime, time as dt_time, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Thêm đường dẫn gốc của dự án vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.settings import MAX_CAMERA_WORKERS, TIMEOUT_SECONDS, LOG_LEVEL, LOG_FORMAT
except ImportError:
    # Fallback values if config is not available
    MAX_CAMERA_WORKERS = 4
    TIMEOUT_SECONDS = 30
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

from services.rtsp_service import rtsp_service
from services.thread_safe_rtsp_service import thread_safe_rtsp_service
from services.database_service import database_service
from db.database import get_connection

# Cấu hình logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class CameraTaskServiceTest:
    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)
        self.max_workers = MAX_CAMERA_WORKERS  # Số lượng thread tối đa để xử lý camera đồng thời
        self.timeout_seconds = TIMEOUT_SECONDS  # Timeout cho mỗi camera
        self.processing_lock = threading.Lock()  # Lock để đảm bảo thread safety
        logger.info(f"Initialized CameraTaskService with {self.max_workers} max workers")

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

    def _process_single_camera(self, camera_info):
        """
        Xử lý một camera đơn lẻ - lấy frame, phát hiện QR và lưu vào database.
        """
        camera_name = camera_info.get('name', 'N/A')
        rtsp_url = camera_info.get('rtsp_url')
        camera_id = camera_info.get('camera_id')
        
        if not rtsp_url:
            logger.warning(f"Camera '{camera_name}' không có rtsp_url. Bỏ qua.")
            return {"success": False, "camera_name": camera_name, "reason": "No RTSP URL"}
        
        try:
            thread_id = threading.current_thread().name
            
            # Thời gian bắt đầu xử lý camera
            camera_start_time = time.time()
            start_dt = datetime.fromtimestamp(camera_start_time)
            logger.info(f"[{thread_id}] 🎬 Bắt đầu xử lý Camera: {camera_name} (ID: {camera_id}) lúc: {start_dt.strftime('%H:%M:%S')}.{start_dt.microsecond//1000:03d}ms")
            logger.info(f"[{thread_id}] 🔗 RTSP URL: {rtsp_url}")
            
            # 1. Lấy frame từ RTSP (sử dụng thread-safe service)
            frame_start_time = time.time()
            frame = thread_safe_rtsp_service.get_frame_from_rtsp(rtsp_url)
            frame_end_time = time.time()
            frame_duration = (frame_end_time - frame_start_time) * 1000

            if frame is not None:
                logger.info(f"[{thread_id}] ✅ Frame đã được lấy thành công trong {frame_duration:.2f}ms")
                
                # 2. Nếu lấy frame thành công, thực hiện nhận diện QR và lưu vào database
                qr_start_time = time.time()
                logger.info(f"[{thread_id}] 🔍 Bắt đầu phát hiện QR cho Camera: {camera_name}")
                newly_found_rois = thread_safe_rtsp_service.qr_detection_saveToDb_safe(frame, camera_id)
                qr_end_time = time.time()
                qr_duration = (qr_end_time - qr_start_time) * 1000
                
                camera_end_time = time.time()
                total_camera_duration = (camera_end_time - camera_start_time) * 1000
                
                if newly_found_rois:
                    logger.info(f"[{thread_id}] 🎯 Các ROI mới tìm thấy cho {camera_name}: {len(newly_found_rois)} QR codes")
                    # Log chi tiết từng QR code
                    for j, detection in enumerate(newly_found_rois):
                        rect, name, roi_width, center_x, center_y = detection
                        logger.info(f"[{thread_id}]   QR {j+1}: {name} - Center: ({center_x}, {center_y}) - Width: {roi_width}")
                    
                    logger.info(f"[{thread_id}] ⏰ Thời gian QR detection: {qr_duration:.2f}ms")
                    logger.info(f"[{thread_id}] ⏰ Tổng thời gian xử lý camera: {total_camera_duration:.2f}ms")
                    end_dt = datetime.fromtimestamp(camera_end_time)
                    logger.info(f"[{thread_id}] 🏁 Kết thúc xử lý Camera: {camera_name} lúc: {end_dt.strftime('%H:%M:%S')}.{end_dt.microsecond//1000:03d}ms (Thành công)")
                    
                    return {
                        "success": True, 
                        "camera_name": camera_name, 
                        "qr_count": len(newly_found_rois),
                        "qr_codes": newly_found_rois,
                        "processing_time": total_camera_duration,
                        "frame_time": frame_duration,
                        "qr_time": qr_duration
                    }
                else:
                    logger.info(f"[{thread_id}] ⚠️ Không tìm thấy ROI mới nào cho {camera_name}.")
                    logger.info(f"[{thread_id}] ⏰ Thời gian QR detection: {qr_duration:.2f}ms")
                    logger.info(f"[{thread_id}] ⏰ Tổng thời gian xử lý camera: {total_camera_duration:.2f}ms")
                    end_dt = datetime.fromtimestamp(camera_end_time)
                    logger.info(f"[{thread_id}] 🏁 Kết thúc xử lý Camera: {camera_name} lúc: {end_dt.strftime('%H:%M:%S')}.{end_dt.microsecond//1000:03d}ms (Không có QR)")
                    
                    return {
                        "success": True, 
                        "camera_name": camera_name, 
                        "qr_count": 0,
                        "qr_codes": [],
                        "processing_time": total_camera_duration,
                        "frame_time": frame_duration,
                        "qr_time": qr_duration
                    }
            else:
                camera_end_time = time.time()
                total_camera_duration = (camera_end_time - camera_start_time) * 1000
                logger.error(f"[{thread_id}] ❌ Không thể lấy frame cho Camera: {camera_name}")
                logger.error(f"[{thread_id}] ⏰ Thời gian xử lý thất bại: {total_camera_duration:.2f}ms")
                end_dt = datetime.fromtimestamp(camera_end_time)
                logger.info(f"[{thread_id}] 🏁 Kết thúc xử lý Camera: {camera_name} lúc: {end_dt.strftime('%H:%M:%S')}.{end_dt.microsecond//1000:03d}ms (Lỗi frame)")
                
                return {
                    "success": False, 
                    "camera_name": camera_name, 
                    "reason": "Cannot get frame",
                    "processing_time": total_camera_duration,
                    "frame_time": frame_duration,
                    "qr_time": 0
                }
                
        except Exception as e:
            error_time = time.time()
            total_error_duration = (error_time - camera_start_time) * 1000
            logger.error(f"[{threading.current_thread().name}] ❌ Lỗi khi xử lý Camera {camera_name}: {e}")
            logger.error(f"[{threading.current_thread().name}] ⏰ Thời gian xử lý lỗi: {total_error_duration:.2f}ms")
            error_dt = datetime.fromtimestamp(error_time)
            logger.info(f"[{threading.current_thread().name}] 🏁 Kết thúc xử lý Camera: {camera_name} lúc: {error_dt.strftime('%H:%M:%S')}.{error_dt.microsecond//1000:03d}ms (Lỗi)")
            
            return {
                "success": False, 
                "camera_name": camera_name, 
                "reason": str(e),
                "processing_time": total_error_duration,
                "frame_time": 0,
                "qr_time": 0
            }

    def _process_cameras(self):
        """
        Xử lý tất cả camera đồng thời - lấy frame, phát hiện QR và lưu vào database.
        """
        logger.info("🚀 Bắt đầu tác vụ: Lấy danh sách camera từ Database.")
        
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                logger.error("❌ Không thể kết nối đến database để lấy danh sách camera.")
                return

            with conn.cursor() as cursor:
                cursor.execute("SELECT name, rtsp_url, camera_id FROM cameras")
                cameras = cursor.fetchall()

            if not cameras:
                logger.warning("⚠️ Không có camera nào được tìm thấy từ Database.")
                return

            logger.info(f"📹 Tìm thấy {len(cameras)} camera. Bắt đầu xử lý đồng thời với {self.max_workers} threads...")
            
            # Thêm thông tin thời gian bắt đầu
            start_time = datetime.now()
            
            # Sử dụng ThreadPoolExecutor để xử lý camera đồng thời
            with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="CameraWorker") as executor:
                # Gửi tất cả các camera vào thread pool
                future_to_camera = {
                    executor.submit(self._process_single_camera, camera): camera 
                    for camera in cameras
                }
                
                # Theo dõi tiến trình và kết quả
                successful_cameras = []
                failed_cameras = []
                total_qr_codes = 0
                total_frame_time = 0
                total_qr_time = 0
                
                # Thêm timeout cho việc xử lý
                for future in as_completed(future_to_camera, timeout=self.timeout_seconds):
                    camera = future_to_camera[future]
                    camera_name = camera.get('name', 'N/A')
                    
                    try:
                        result = future.result()
                        if result["success"]:
                            successful_cameras.append(camera_name)
                            total_qr_codes += result.get("qr_count", 0)
                            total_frame_time += result.get("frame_time", 0)
                            total_qr_time += result.get("qr_time", 0)
                        else:
                            failed_cameras.append({
                                "name": camera_name,
                                "reason": result.get("reason", "Unknown error"),
                                "processing_time": result.get("processing_time", 0)
                            })
                    except Exception as e:
                        logger.error(f"❌ Lỗi khi xử lý camera {camera_name}: {e}")
                        failed_cameras.append({
                            "name": camera_name,
                            "reason": str(e),
                            "processing_time": 0
                        })
                
                # Tính toán thời gian xử lý
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Tổng kết kết quả
                logger.info(f"🎉 Hoàn thành xử lý {len(cameras)} camera trong {processing_time:.2f} giây ({processing_time*1000:.2f}ms):")
                logger.info(f"  ✅ Thành công: {len(successful_cameras)} camera")
                logger.info(f"  🔍 Tổng QR codes tìm thấy: {total_qr_codes}")
                logger.info(f"  ⏰ Tổng thời gian frame: {total_frame_time:.2f}ms")
                logger.info(f"  ⏰ Tổng thời gian QR detection: {total_qr_time:.2f}ms")
                logger.info(f"  ⏰ Thời gian trung bình/camera: {(processing_time*1000)/len(cameras):.2f}ms")
                logger.info(f"  🏁 Kết thúc tất cả camera lúc: {end_time.strftime('%H:%M:%S')}.{end_time.microsecond//1000:03d}ms")
                
                if successful_cameras:
                    logger.info(f"  📹 Camera thành công: {', '.join(successful_cameras)}")
                
                if failed_cameras:
                    logger.warning(f"  ❌ Thất bại: {len(failed_cameras)} camera")
                    for failed_camera in failed_cameras:
                        logger.warning(f"    - {failed_camera['name']}: {failed_camera['reason']} (Thời gian: {failed_camera['processing_time']:.2f}ms)")

        except Exception as e:
            logger.error(f"❌ Lỗi không xác định trong tác vụ: {e}")
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
