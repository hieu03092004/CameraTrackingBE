#!/usr/bin/env python3
"""
Script test để kiểm tra RTSP service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rtsp_service import rtsp_service
import cv2
def test_rtsp_frame():
    """
    Test hàm lấy frame từ RTSP
    """
    # RTSP URL của bạn
    rtsp_url = "rtsp://admin:Imou0588!@192.168.1.103:554/cam/realmonitor?channel=1&subtype=0"
    
    print(f"Đang thử kết nối đến: {rtsp_url}")
    
    # Lấy frame
    frame = rtsp_service.get_frame_from_rtsp(rtsp_url)
    
    if frame is not None:
        print("✅ Lấy frame thành công!")
        
        # In thông tin frame
        frame_info = rtsp_service.get_frame_info(frame)
        print(f"📊 Thông tin frame:")
        print(f"   - Kích thước: {frame_info['shape']}")
        print(f"   - Kiểu dữ liệu: {frame_info['dtype']}")
        print(f"   - Kích thước (bytes): {frame_info['size_bytes']}")
        print(f"   - Số kênh màu: {frame_info['channels']}")
        
        # Lưu frame để xem
        output_path = "test_frame.jpg"
        cv2.imwrite(output_path, frame)
        print(f"💾 Đã lưu frame vào: {output_path}")
        
        return True
    else:
        print("❌ Không thể lấy frame từ RTSP stream")
        return False

if __name__ == "__main__":
    print("🚀 Bắt đầu test RTSP service...")
    success = test_rtsp_frame()
    
    if success:
        print("✅ Test hoàn thành thành công!")
    else:
        print("❌ Test thất bại!")
