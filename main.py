from fastapi import FastAPI
from api.index import router
from contextlib import asynccontextmanager
from task.task_services import camera_task_service
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động các dịch vụ nền khi app bắt đầu
    camera_task_service.start()
    yield
    # Dừng các dịch vụ nền khi app kết thúc
    camera_task_service.stop()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include tất cả routes từ index.routes
app.include_router(router)