from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from db.database import get_connection
from schemas.camera_schema import CameraOut, CameraCreate
import asyncio
import subprocess

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

@router.websocket("/ws/stream/{camera_id}")
async def stream_rtsp(websocket: WebSocket, camera_id: int):
    await websocket.accept()

    # 🔍 Truy vấn URL từ DB
    conn = get_connection()
    if conn is None:
        await websocket.close(code=1011)
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT rtsp_url FROM cameras WHERE camera_id = %s", (camera_id,))
            result = cursor.fetchone()
            if not result:
                await websocket.send_text(f"❌ Không tìm thấy camera với ID {camera_id}")
                await websocket.close(code=1008)
                return
            rtsp_url = result["rtsp_url"]
            print(f"[Camera {camera_id}] URL: {rtsp_url}")
    except Exception as e:
        print(f"Lỗi khi truy vấn DB: {e}")
        await websocket.send_text("❌ Lỗi truy vấn DB")
        await websocket.close(code=1011)
        return
    finally:
        conn.close()

    # 🛠️ Khởi tạo ffmpeg
    process = subprocess.Popen(
        [
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "-i", rtsp_url,
            "-f", "mjpeg",
            "-q:v", "5",
            "-r", "10",
            "-"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    buffer = b""
    jpeg_start = b"\xff\xd8"
    jpeg_end = b"\xff\xd9"

    # ✅ Tạo task phụ để lắng nghe disconnect từ client
    async def detect_disconnect():
        try:
            while True:
                await websocket.receive()  # chỉ cần lắng nghe để BE biết client đã disconnect
        except WebSocketDisconnect:
            print(f"Client disconnected from camera {camera_id}")
        except Exception as e:
            print(f"[detect_disconnect] Lỗi khi nhận: {e}")

    disconnect_task = asyncio.create_task(detect_disconnect())

    try:
        while True:
            if disconnect_task.done():
                print(f"⚠️ Phát hiện disconnect từ client (camera {camera_id})")
                break

            data = await asyncio.to_thread(process.stdout.read, 4096)
            if not data:
                break
            buffer += data

            while True:
                start = buffer.find(jpeg_start)
                end = buffer.find(jpeg_end, start)
                if start != -1 and end != -1:
                    frame = buffer[start:end + 2]
                    await websocket.send_bytes(frame)
                    buffer = buffer[end + 2:]
                else:
                    break

            await asyncio.sleep(0)  # nhường event loop, tránh chặn

    except Exception as e:
        print(f"Streaming error (camera {camera_id}): {e}")

    finally:
        print(f"🧹 Đóng stream cho camera {camera_id}")

        if process and process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                print("⚠️ Không thể kill ffmpeg đúng cách")

        if not websocket.client_state.name == "DISCONNECTED":
            try:
                await websocket.close()
            except Exception as e:
                print("WebSocket close error:", e)

        if not disconnect_task.done():
            disconnect_task.cancel()
