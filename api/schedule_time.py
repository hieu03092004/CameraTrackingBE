from typing import List

from fastapi import APIRouter, HTTPException
from db.database import get_connection
from schemas.schedule_schema import ScheduleTimeOut

router = APIRouter()

@router.get("/schedule-times", response_model=List[ScheduleTimeOut])
def get_schedule_times():
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT schedule_time_id, capture_time, is_active FROM schedule_times ORDER BY capture_time")
            result = cursor.fetchall()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

@router.put("/schedule-times/{schedule_time_id}")
def update_schedule_time(schedule_time_id: int, is_active: bool):
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE schedule_times SET is_active = %s WHERE schedule_time_id = %s",
                (is_active, schedule_time_id)
            )
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Schedule time not found")

        return {"message": "Schedule time updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

