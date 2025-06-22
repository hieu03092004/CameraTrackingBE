import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    user=os.getenv('MYSQL_USERNAME', 'root'),
    password=os.getenv('MYSQL_PASSWORD', ''),
    database=os.getenv('DATABASE_NAME', 'camera_tracking'),
    port=int(os.getenv('MYSQL_PORT', '3306')),
    cursorclass=DictCursor
)
