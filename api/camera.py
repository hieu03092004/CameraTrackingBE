from fastapi import APIRouter
from db.database import conn

router = APIRouter()

@router.get("/cameras")
def get_cameras():
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM cameras")
        result = cursor.fetchall()
    return result
