from fastapi import FastAPI
from .index import router

app = FastAPI()

# Include tất cả routes từ index.routes
app.include_router(router)

# Có thể thêm các routes khác ở đây nếu cần
# app.include_router(other_router) 