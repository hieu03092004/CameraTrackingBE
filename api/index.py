from fastapi import APIRouter
from .camera import router as camera_router
from .schedule_time import router as schedule_time_router
from .settlement_chart import router as settlement_chart_router

# Tạo router tổng
router = APIRouter()

# Định nghĩa prefix cho các routes
API_PREFIX = "/api/v1"

router.include_router(
    camera_router,
    prefix=f"{API_PREFIX}",
    tags=["camera"]
)

router.include_router(
    schedule_time_router,
    prefix=f"{API_PREFIX}",
    tags=["schedule"]
)

router.include_router(
    settlement_chart_router,
    prefix=f"{API_PREFIX}",
    tags=["settlement-chart"]
)
