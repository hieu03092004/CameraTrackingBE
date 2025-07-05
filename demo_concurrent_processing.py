"""
Demo script để kiểm tra hệ thống xử lý đồng thời camera
"""
import sys
import os
import time
from datetime import datetime

# Thêm đường dẫn gốc của dự án vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task.test_task import camera_task_service
from db.database import get_connection

def check_database_connection():
    """Kiểm tra kết nối database"""
    print("🔍 Kiểm tra kết nối database...")
    conn = get_connection()
    if conn:
        print("✅ Database connection: OK")
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM cameras")
            result = cursor.fetchone()
            camera_count = result['count']
            print(f"📹 Số lượng camera trong database: {camera_count}")
        conn.close()
        return camera_count
    else:
        print("❌ Database connection: FAILED")
        return 0

def demo_sequential_vs_concurrent():
    """Demo so sánh xử lý tuần tự vs đồng thời"""
    print("\n" + "="*60)
    print("🚀 DEMO: So sánh xử lý tuần tự vs đồng thời")
    print("="*60)
    
    camera_count = check_database_connection()
    
    if camera_count == 0:
        print("❌ Không có camera nào để test. Vui lòng thêm camera vào database.")
        return
    
    print(f"\n📊 Sẽ xử lý {camera_count} camera...")
    print(f"🔧 Cấu hình: {camera_task_service.max_workers} workers, timeout {camera_task_service.timeout_seconds}s")
    
    # Test xử lý đồng thời
    print(f"\n⏱️ Bắt đầu xử lý đồng thời lúc: {datetime.now().strftime('%H:%M:%S')}")
    start_time = time.time()
    
    try:
        camera_task_service._process_cameras()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n⏱️ Kết thúc xử lý lúc: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⚡ Tổng thời gian xử lý: {processing_time:.2f} giây")
        print(f"📈 Trung bình: {processing_time/camera_count:.2f} giây/camera")
        
        # Ước tính thời gian xử lý tuần tự
        estimated_sequential_time = processing_time * camera_count / camera_task_service.max_workers
        print(f"🐌 Ước tính thời gian tuần tự: {estimated_sequential_time:.2f} giây")
        
        if estimated_sequential_time > processing_time:
            improvement = ((estimated_sequential_time - processing_time) / estimated_sequential_time) * 100
            print(f"🎯 Cải thiện hiệu suất: {improvement:.1f}%")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình xử lý: {e}")
        import traceback
        traceback.print_exc()

def demo_thread_info():
    """Demo thông tin về threading"""
    print("\n" + "="*60)
    print("🧵 THÔNG TIN THREADING")
    print("="*60)
    
    import threading
    
    print(f"📊 Số thread hiện tại: {threading.active_count()}")
    print(f"🔧 Max workers: {camera_task_service.max_workers}")
    print(f"⏱️ Timeout: {camera_task_service.timeout_seconds} giây")
    
    print("\n🔍 Danh sách threads:")
    for thread in threading.enumerate():
        status = "🟢 Alive" if thread.is_alive() else "🔴 Dead"
        print(f"  - {thread.name}: {status}")

if __name__ == "__main__":
    try:
        print("🎬 DEMO: Hệ thống xử lý đồng thời camera")
        print("="*60)
        
        demo_thread_info()
        demo_sequential_vs_concurrent()
        
        print("\n" + "="*60)
        print("✅ Demo hoàn thành!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n❌ Demo bị dừng bởi user")
    except Exception as e:
        print(f"\n❌ Lỗi trong demo: {e}")
        import traceback
        traceback.print_exc()
