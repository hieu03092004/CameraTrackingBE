# Camera Tracking Backend - Xử lý đồng thời

## Tổng quan về cải tiến

Hệ thống đã được cải tiến để xử lý **đồng thời** nhiều camera thay vì xử lý **tuần tự**. Điều này giúp:

- ⚡ **Tăng tốc độ xử lý**: Tất cả camera sẽ được xử lý cùng một lúc
- 🔧 **Tối ưu hiệu suất**: Sử dụng ThreadPoolExecutor để quản lý threads
- 🛡️ **Thread-safe**: Đảm bảo an toàn khi xử lý đồng thời với database

## Các thành phần chính

### 1. CameraTaskServiceTest (Cải tiến)
- Sử dụng `ThreadPoolExecutor` để xử lý đồng thời
- Cấu hình số lượng thread worker tối đa
- Timeout cho việc xử lý camera
- Logging chi tiết cho từng thread

### 2. ThreadSafeRTSPService (Mới)
- Service RTSP thread-safe
- Không sử dụng instance variables để tránh xung đột
- Logging với thread ID

### 3. ThreadSafeDatabaseService (Mới)
- Service database thread-safe
- Tạo connection mới cho mỗi operation
- Context manager để quản lý connection

### 4. Configuration (Mới)
- File cấu hình `config/settings.py`
- Điều chỉnh số lượng worker threads
- Timeout settings

## Cách sử dụng

### 1. Cấu hình
Chỉnh sửa file `config/settings.py`:

```python
# Threading configuration
MAX_CAMERA_WORKERS = 4  # Số lượng camera xử lý đồng thời
TIMEOUT_SECONDS = 30    # Timeout cho mỗi camera
```

### 2. Chạy hệ thống
```bash
# Chạy main application
python main.py

# Test xử lý đồng thời
python test_concurrent_cameras.py
```

### 3. Theo dõi logs
Logs sẽ hiển thị:
- `[CameraWorker-X]` - Thread ID đang xử lý
- Thời gian xử lý cho từng camera
- Tổng kết kết quả

## Lợi ích

### So sánh hiệu suất
- **Trước (tuần tự)**: 2 camera × 10 giây = 20 giây
- **Sau (đồng thời)**: 2 camera × 10 giây = ~10 giây (với 2+ threads)

### Tính năng mới
- 🔄 **Xử lý đồng thời**: Tất cả camera chạy cùng lúc
- 📊 **Thống kê chi tiết**: Thời gian xử lý, số QR codes tìm thấy
- 🛡️ **Thread-safe**: An toàn với database và RTSP
- ⚙️ **Cấu hình linh hoạt**: Điều chỉnh số workers theo nhu cầu

## Cấu trúc mới

```
CameraTrackingBE/
├── config/
│   ├── __init__.py
│   └── settings.py              # Cấu hình hệ thống
├── services/
│   ├── thread_safe_rtsp_service.py    # RTSP service thread-safe
│   └── thread_safe_db_service.py      # Database service thread-safe
├── task/
│   └── test_task.py            # Task service với threading
└── test_concurrent_cameras.py  # Script test
```

## Lưu ý quan trọng

1. **Database Connection**: Mỗi thread tạo connection riêng
2. **RTSP Timeout**: Có thể điều chỉnh timeout cho RTSP stream
3. **Thread Workers**: Số lượng tối đa phụ thuộc vào tài nguyên hệ thống
4. **Error Handling**: Lỗi ở một camera không ảnh hưởng đến camera khác

## Troubleshooting

### Nếu gặp lỗi database connection:
- Kiểm tra connection pool settings
- Tăng timeout cho database connection

### Nếu RTSP stream không ổn định:
- Giảm số lượng MAX_CAMERA_WORKERS
- Tăng RTSP_TIMEOUT trong config

### Nếu hiệu suất không tăng:
- Kiểm tra số lượng CPU cores
- Điều chỉnh MAX_CAMERA_WORKERS phù hợp
