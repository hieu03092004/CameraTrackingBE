from fastapi import APIRouter
from .checkv1 import router as test_router
from .camera import router as camera_router

# Tạo router tổng
router = APIRouter()

# Định nghĩa prefix cho các routes
API_PREFIX = "/api/v1"

# Include các routes con
router.include_router(
    test_router,
    prefix=f"{API_PREFIX}",
    tags=["checkv1"]
)

router.include_router(
    camera_router,
    prefix=f"{API_PREFIX}",
    tags=["camera"]
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