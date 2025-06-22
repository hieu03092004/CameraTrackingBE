from fastapi import APIRouter, HTTPException
from db.database import get_connection
from schemas.camera_schema import CameraOut, CameraCreate

router = APIRouter()
@router.get("/cameras")
def get_cameras():
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM cameras")
            result = cursor.fetchall()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

@router.post("/cameras", response_model=CameraOut)
def create_camera(camera: CameraCreate):
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="❌ Không kết nối được DB")

    try:
        with conn.cursor() as cursor:
            insert_query = """
                INSERT INTO cameras (name, rtsp_url, conversion_rate)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (camera.name, camera.rtsp_url, camera.conversion_rate))
            conn.commit()
            camera_id = cursor.lastrowid

            return {
                "camera_id": camera_id,
                "name": camera.name,
                "rtsp_url": camera.rtsp_url,
                "conversion_rate": camera.conversion_rate
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thêm camera: {e}")
    finally:
        conn.close()
