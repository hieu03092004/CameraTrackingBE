"""
Configuration file for camera task service
"""

# Threading configuration
MAX_CAMERA_WORKERS = 4  # Số lượng camera có thể xử lý đồng thời
TIMEOUT_SECONDS = 30     # Timeout cho việc xử lý một camera

# Database configuration
DB_CONNECTION_POOL_SIZE = 10  # Số lượng connection tối đa trong pool
DB_CONNECTION_TIMEOUT = 30    # Timeout cho database connection

# RTSP configuration
RTSP_TIMEOUT = 15  # Timeout cho RTSP stream
RTSP_BUFFER_SIZE = 1  # Buffer size cho RTSP stream

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
