from fastapi import APIRouter
from api.routes.get import router as test_router
from api.routes.rtsp import router as rtsp_router

# Tạo router tổng
router = APIRouter()

# Định nghĩa prefix cho các routes
API_PREFIX = "/api/v1"

# Include các routes con
router.include_router(
    test_router,
    prefix=f"{API_PREFIX}",
    tags=["getFrame"]
)

router.include_router(
    rtsp_router,
    prefix=f"{API_PREFIX}/rtsp",
    tags=["rtsp"]
)

# Có thể thêm các routes khác ở đây
# router.include_router(
#     auth_router,
#     prefix=f"{API_PREFIX}/auth",
#     tags=["auth"]
# )

# router.include_router(
#     dashboard_router,
#     prefix=f"{API_PREFIX}/dashboard",
#     tags=["dashboard"]
# )
