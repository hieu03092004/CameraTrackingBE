import sys
import os
from datetime import datetime, time
from typing import List, Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import get_connection

class DatabaseService:
    """Service để tương tác với database sử dụng PyMySQL trực tiếp"""
    
    def __init__(self):
        self.connection = get_connection()
    
    
    
    # ==================== CAMERA OPERATIONS ====================
    
    
    def get_all_cameras(self) -> List[Dict]:
        """Lấy tất cả cameras"""
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM cameras")
            cameras = []
            for row in cursor.fetchall():
                cameras.append({
                    "camera_id": row["camera_id"],
                    "name": row["name"],
                    "rtsp_url": row["rtsp_url"],
                    "conversion_rate": row["conversion_rate"]
                })
            cursor.close()
            return cameras
        except Exception as e:
            print(f"❌ Lỗi khi lấy cameras: {e}")
            return []
    
    def get_camera_by_id(self, camera_id: int) -> Optional[Dict]:
        """Lấy camera theo ID"""
        if not self.connection:
            return None
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM cameras WHERE camera_id = %s", (camera_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return {
                    "camera_id": row["camera_id"],
                    "name": row["name"],
                    "rtsp_url": row["rtsp_url"],
                    "conversion_rate": row["conversion_rate"]
                }
            return None
        except Exception as e:
            print(f"❌ Lỗi khi lấy camera: {e}")
            return None
    
    # ==================== SCHEDULE TIME OPERATIONS ====================
    
    
    
    def get_active_schedules(self) -> List[Dict]:
        """Lấy tất cả lịch chụp đang hoạt động"""
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM schedule_times WHERE is_active = TRUE")
            schedules = []
            for row in cursor.fetchall():
                schedules.append({
                    "schedule_time_id": row["schedule_time_id"],
                    "capture_time": row["capture_time"],
                    "is_active": row["is_active"]
                })
            cursor.close()
            return schedules
        except Exception as e:
            print(f"❌ Lỗi khi lấy lịch chụp: {e}")
            return []
    
    # ==================== QR CODE OPERATIONS ====================
    
    def create_qr_code(self, name_roi: str, initial_x: int, initial_y: int) -> Optional[Dict]:
        """Tạo QR code mới"""
        if not self.connection:
            return None
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO qr_codes (name_roi, initial_x, initial_y) VALUES (%s, %s, %s)",
                (name_roi, initial_x, initial_y)
            )
            self.connection.commit()
            qr_code_id = cursor.lastrowid
            cursor.close()
            
            print(f"✅ Đã tạo QR code: {name_roi}")
            return {
                "qr_code_id": qr_code_id,
                "name_roi": name_roi,
                "initial_x": initial_x,
                "initial_y": initial_y,
            }
        except Exception as e:
            print(f"❌ Lỗi khi tạo QR code: {e}")
            return None
    
    def get_qr_code_by_name(self, name_roi: str) -> Optional[Dict]:
        """Lấy QR code theo tên"""
        if not self.connection:
            return None
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM qr_codes WHERE name_roi = %s", (name_roi,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return {
                    "qr_code_id": row["qr_code_id"],
                    "name_roi": row["name_roi"],
                    "initial_x": row["initial_x"],
                    "initial_y": row["initial_y"],
                    "initial_time": row["initial_time"]
                }
            return None
        except Exception as e:
            print(f"❌ Lỗi khi lấy QR code: {e}")
            return None
    
    def get_all_qr_codes(self) -> List[Dict]:
        """Lấy tất cả QR codes"""
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM qr_codes")
            qr_codes = []
            for row in cursor.fetchall():
                qr_codes.append({
                    "qr_code_id": row["qr_code_id"],
                    "name_roi": row["name_roi"],
                    "initial_x": row["initial_x"],
                    "initial_y": row["initial_y"],
                    "initial_time": row["initial_time"]
                })
            cursor.close()
            return qr_codes
        except Exception as e:
            print(f"❌ Lỗi khi lấy QR codes: {e}")
            return []
    
    # ==================== MEASUREMENT OPERATIONS ====================
    
    def create_measurement(self, x: int, y: int, qr_code_id: Optional[int] = None) -> Optional[Dict]:
        """Tạo measurement mới"""
        if not self.connection:
            return None
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO measurements (x, y, qr_code_id) VALUES (%s, %s, %s)",
                (x, y, qr_code_id)
            )
            self.connection.commit()
            measurement_id = cursor.lastrowid
            cursor.close()
            
            print(f"✅ Đã tạo measurement: ({x}, {y})")
            return {
                "measurement_id": measurement_id,
                "x": x,
                "y": y,
                "qr_code_id": qr_code_id,
            }
        except Exception as e:
            print(f"❌ Lỗi khi tạo measurement: {e}")
            return None
    
    def get_measurements_by_qr_code(self, qr_code_id: int, limit: int = 100) -> List[Dict]:
        """Lấy measurements theo QR code ID"""
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM measurements WHERE qr_code_id = %s ORDER BY tracking_time DESC LIMIT %s",
                (qr_code_id, limit)
            )
            measurements = []
            for row in cursor.fetchall():
                measurements.append({
                    "measurement_id": row["measurement_id"],
                    "x": row["x"],
                    "y": row["y"],
                    "qr_code_id": row["qr_code_id"],
                    "tracking_time": row["tracking_time"]
                })
            cursor.close()
            return measurements
        except Exception as e:
            print(f"❌ Lỗi khi lấy measurements: {e}")
            return []
    
    def get_measurements_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Lấy measurements trong khoảng thời gian"""
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM measurements WHERE tracking_time BETWEEN %s AND %s ORDER BY tracking_time DESC",
                (start_time, end_time)
            )
            measurements = []
            for row in cursor.fetchall():
                measurements.append({
                    "measurement_id": row["measurement_id"],
                    "x": row["x"],
                    "y": row["y"],
                    "qr_code_id": row["qr_code_id"],
                    "tracking_time": row["tracking_time"]
                })
            cursor.close()
            return measurements
        except Exception as e:
            print(f"❌ Lỗi khi lấy measurements: {e}")
            return []

# Tạo instance global
database_service = DatabaseService() 