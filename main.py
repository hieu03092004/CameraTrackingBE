from fastapi import FastAPI
from api.index import router

app = FastAPI()

# Include tất cả routes từ index.routes
app.include_router(router)