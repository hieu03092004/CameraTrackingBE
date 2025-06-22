from fastapi import APIRouter, Query, HTTPException
from typing import List, Literal, Dict
from datetime import datetime
from db.database import get_connection

router = APIRouter()

@router.get("/settlement-chart")
def get_settlement_chart(
    qr_code_id_movable: int,
    qr_code_id_fixed: int,
    camera_id_movable: int,
    camera_id_fixed: int,
    interval: Literal["hour", "day", "month", "year"] = "hour",
    time_from: datetime = Query(..., description="Start time (ISO format)"),
    time_to: datetime = Query(..., description="End time (ISO format)")
) -> List[Dict]:
    """
    Trả về dữ liệu vẽ biểu đồ độ lún theo công thức tổng quát, nhóm theo giờ/ngày/tháng/năm.
    """
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        with conn.cursor() as cursor:
            # Lấy conversion_rate cho 2 camera
            cursor.execute("SELECT camera_id, conversion_rate FROM cameras WHERE camera_id IN (%s, %s)",
                           (camera_id_movable, camera_id_fixed))
            rates = {row['camera_id']: float(row['conversion_rate']) for row in cursor.fetchall()}
            Sb = rates.get(camera_id_movable)
            Sa = rates.get(camera_id_fixed)
            if Sb is None or Sa is None:
                raise HTTPException(status_code=400, detail="Không tìm thấy thông tin conversion_rate của camera")

            # Lấy initial_y cho 2 QR
            cursor.execute("SELECT qr_code_id, initial_y FROM qr_codes WHERE qr_code_id IN (%s, %s)",
                           (qr_code_id_movable, qr_code_id_fixed))
            initials = {row['qr_code_id']: row['initial_y'] for row in cursor.fetchall()}
            ym0 = initials.get(qr_code_id_movable)
            yr0 = initials.get(qr_code_id_fixed)
            if ym0 is None or yr0 is None:
                raise HTTPException(status_code=400, detail="Không tìm thấy initial_y của QR")

            # Group by interval (hour/day/...)
            if interval == "hour":
                group_format = "%Y-%m-%d %H:00:00"
            elif interval == "day":
                group_format = "%Y-%m-%d 00:00:00"
            elif interval == "month":
                group_format = "%Y-%m-01 00:00:00"
            elif interval == "year":
                group_format = "%Y-01-01 00:00:00"
            else:
                group_format = "%Y-%m-%d %H:00:00"

            # Lấy measurements cho movable QR
            cursor.execute(f"""
                SELECT 
                    DATE_FORMAT(tracking_time, '{group_format}') as time_group,
                    AVG(y) as ym
                FROM measurements
                WHERE qr_code_id=%s AND tracking_time BETWEEN %s AND %s
                GROUP BY time_group
                ORDER BY time_group
            """, (qr_code_id_movable, time_from, time_to))
            movable_data = {row['time_group']: row['ym'] for row in cursor.fetchall()}

            # Lấy measurements cho fixed QR
            cursor.execute(f"""
                SELECT 
                    DATE_FORMAT(tracking_time, '{group_format}') as time_group,
                    AVG(y) as yr
                FROM measurements
                WHERE qr_code_id=%s AND tracking_time BETWEEN %s AND %s
                GROUP BY time_group
                ORDER BY time_group
            """, (qr_code_id_fixed, time_from, time_to))
            fixed_data = {row['time_group']: row['yr'] for row in cursor.fetchall()}

            # Lấy tất cả các mốc thời gian chung
            all_time_points = sorted(set(movable_data.keys()) | set(fixed_data.keys()))

            # Tính toán độ lún tại từng time_point
            result = []
            for time_group in all_time_points:
                ym = movable_data.get(time_group, ym0)  # Nếu thiếu thì lấy giá trị ban đầu
                yr = fixed_data.get(time_group, yr0)
                lun = (ym - ym0) * Sb - (yr - yr0) * Sa
                result.append({
                    "time": time_group,
                    "settlement": lun
                })
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()