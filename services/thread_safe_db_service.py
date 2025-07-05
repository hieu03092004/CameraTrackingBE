"""
Thread-safe database service for concurrent camera processing
"""
import threading
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
from db.database import get_connection
from datetime import datetime, time
logger = logging.getLogger(__name__)

class ThreadSafeDatabaseService:
    """
    Thread-safe database service sử dụng connection mới cho mỗi operation
    thay vì chia sẻ connection giữa các threads.
    """
    
    def __init__(self):
        self._local = threading.local()
        logger.info("Initialized ThreadSafeDatabaseService")
    
    @contextmanager
    def get_db_connection(self):
        """
        Context manager để tạo và quản lý database connection
        """
        conn = None
        try:
            conn = get_connection()
            if conn is None:
                raise Exception("Cannot establish database connection")
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def create_qr_code_safe(self, name_roi: str, initial_x: int, initial_y: int) -> Optional[Dict[str, Any]]:
        """
        Thread-safe method to create QR code
        """
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    current_time = datetime.now()
                    query = """
                    INSERT INTO qr_codes (name_roi, initial_x, initial_y,initial_time)
                    VALUES (%s, %s, %s,%s)
                    """
                    cursor.execute(query, (name_roi, initial_x, initial_y, current_time))
                    conn.commit()
                    
                    # Lấy ID của QR code vừa tạo
                    qr_code_id = cursor.lastrowid
                    
                    return {
                        "qr_code_id": qr_code_id,
                        "name_roi": name_roi,
                        "initial_x": initial_x,
                        "initial_y": initial_y
                    }
        except Exception as e:
            logger.error(f"Error creating QR code: {e}")
            return None
    
    def get_qr_code_by_id_safe(self, qr_code_id: int) -> Optional[Dict[str, Any]]:
        """
        Thread-safe method to get QR code by ID
        """
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    query = "SELECT * FROM qr_codes WHERE qr_code_id = %s"
                    cursor.execute(query, (qr_code_id,))
                    row = cursor.fetchone()
                    
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
            logger.error(f"Error getting QR code by ID: {e}")
            return None
    
    def create_measurement_safe(self, x: int, y: int, qr_code_id: int) -> Optional[Dict[str, Any]]:
        """
        Thread-safe method to create measurement
        """
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    current_time = datetime.now()
                    query = """
                    INSERT INTO measurements (x, y, qr_code_id,tracking_time)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(query, (x, y, qr_code_id,current_time))
                    conn.commit()
                    
                    # Lấy ID của measurement vừa tạo
                    measurement_id = cursor.lastrowid
                    
                    return {
                        "measurement_id": measurement_id,
                        "x": x,
                        "y": y,
                        "qr_code_id": qr_code_id
                    }
        except Exception as e:
            logger.error(f"Error creating measurement: {e}")
            return None
    
    def check_camera_roi_exists_safe(self, camera_id: int) -> bool:
        """
        Thread-safe method to check if camera ROI exists
        """
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    query = "SELECT COUNT(*) as count FROM qr_codes WHERE qr_code_id = %s"
                    cursor.execute(query, (camera_id,))
                    result = cursor.fetchone()
                    return result["count"] > 0
        except Exception as e:
            logger.error(f"Error checking camera ROI exists: {e}")
            return False
    
    def check_qr_name_exists_safe(self, name_roi: str) -> bool:
        """
        Thread-safe method to check if QR name exists
        """
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    query = "SELECT COUNT(*) as count FROM qr_codes WHERE name_roi = %s"
                    cursor.execute(query, (name_roi,))
                    result = cursor.fetchone()
                    return result["count"] > 0
        except Exception as e:
            logger.error(f"Error checking QR name exists: {e}")
            return False
    
    def get_qr_code_by_name_safe(self, name_roi: str) -> Optional[Dict[str, Any]]:
        """
        Thread-safe method to get QR code by name
        """
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    query = "SELECT * FROM qr_codes WHERE name_roi = %s"
                    cursor.execute(query, (name_roi,))
                    row = cursor.fetchone()
                    
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
            logger.error(f"Error getting QR code by name: {e}")
            return None

# Tạo instance global
thread_safe_db_service = ThreadSafeDatabaseService()
