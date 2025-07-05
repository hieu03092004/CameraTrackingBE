"""
Demo script để test và lưu frame với ROI visualization
"""
import sys
import os
import time
from datetime import datetime

# Thêm đường dẫn gốc của dự án vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task.test_task import camera_task_service
from db.database import get_connection

def check_output_directory():
    """Kiểm tra và tạo thư mục output"""
    output_dir = "captured_frames"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ Đã tạo thư mục: {output_dir}")
    else:
        print(f"✅ Thư mục đã tồn tại: {output_dir}")
    
    return output_dir

def demo_capture_frames_with_roi():
    """Demo chụp và lưu frame với ROI"""
    print("\n" + "="*60)
    print("📸 DEMO: Chụp frame và vẽ ROI")
    print("="*60)
    
    # Kiểm tra thư mục output
    output_dir = check_output_directory()
    
    # Kiểm tra database
    conn = get_connection()
    if not conn:
        print("❌ Không thể kết nối database")
        return
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM cameras")
        result = cursor.fetchone()
        camera_count = result['count']
        print(f"📹 Số lượng camera trong database: {camera_count}")
    conn.close()
    
    if camera_count == 0:
        print("❌ Không có camera nào để test")
        return
    
    print(f"🔧 Cấu hình: {camera_task_service.max_workers} workers")
    print(f"📁 Thư mục lưu frame: {output_dir}")
    
    # Xóa các file cũ trong thư mục (tùy chọn)
    existing_files = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
    if existing_files:
        print(f"🗑️ Tìm thấy {len(existing_files)} file cũ trong thư mục")
        for file in existing_files:
            os.remove(os.path.join(output_dir, file))
        print("✅ Đã xóa các file cũ")
    
    print(f"\n⏱️ Bắt đầu chụp frame lúc: {datetime.now().strftime('%H:%M:%S')}")
    start_time = time.time()
    
    try:
        camera_task_service._process_cameras()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n⏱️ Kết thúc chụp lúc: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⚡ Tổng thời gian: {processing_time:.2f} giây")
        
        # Kiểm tra file đã được tạo
        new_files = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
        if new_files:
            print(f"\n📸 Đã tạo {len(new_files)} file frame:")
            for file in sorted(new_files):
                file_path = os.path.join(output_dir, file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"  - {file} ({file_size:.1f} KB)")
            
            print(f"\n📁 Đường dẫn đầy đủ: {os.path.abspath(output_dir)}")
            print("✅ Bạn có thể mở các file này để kiểm tra ROI và center points!")
        else:
            print("\n⚠️ Không có file frame nào được tạo (có thể không phát hiện QR)")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình chụp: {e}")
        import traceback
        traceback.print_exc()

def demo_frame_info():
    """Demo thông tin về frame capture"""
    print("\n" + "="*60)
    print("📊 THÔNG TIN FRAME CAPTURE")
    print("="*60)
    
    output_dir = "captured_frames"
    
    print(f"📁 Thư mục output: {output_dir}")
    print(f"🎨 Màu sắc:")
    print(f"  - ROI rectangle: Xanh lá (Green)")
    print(f"  - Center point: Đỏ (Red)")
    print(f"  - Text: Trắng (White)")
    print(f"  - Info: Vàng (Yellow)")
    
    print(f"\n📝 Thông tin sẽ được vẽ:")
    print(f"  - QR code name")
    print(f"  - Tọa độ center (x, y)")
    print(f"  - Kích thước ROI")
    print(f"  - Camera ID và Thread ID")
    print(f"  - Timestamp")

if __name__ == "__main__":
    try:
        print("📸 DEMO: Chụp frame với ROI visualization")
        print("="*60)
        
        demo_frame_info()
        demo_capture_frames_with_roi()
        
        print("\n" + "="*60)
        print("✅ Demo hoàn thành!")
        print("📁 Kiểm tra thư mục 'captured_frames' để xem kết quả!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n❌ Demo bị dừng bởi user")
    except Exception as e:
        print(f"\n❌ Lỗi trong demo: {e}")
        import traceback
        traceback.print_exc()
