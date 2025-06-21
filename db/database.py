import pymysql
from pymysql.cursors import DictCursor

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='camera_tracking_system',
    port=3306,
    cursorclass=DictCursor
)
