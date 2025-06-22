import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# Load file env thay vì .env
load_dotenv('.env')

def get_connection():
    """Tạo connection đến database"""
    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USERNAME', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('DATABASE_NAME', 'camera_tracking_system'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            cursorclass=DictCursor
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Tạo connection mặc định (có thể None nếu không kết nối được)
conn = get_connection()
