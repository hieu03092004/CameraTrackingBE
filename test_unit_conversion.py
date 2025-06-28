#!/usr/bin/env python3
"""
Script test cho hàm process_unit_conversion mới
"""

import sys
import os

# Thêm đường dẫn để import các module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rtsp_service import rtsp_service

def test_process_unit_conversion():
    """Test hàm process_unit_conversion với RTSP URL thật"""
    print("🚀 Bắt đầu test process_unit_conversion...")
    print("="*60)
    
    # Thông số test
    rtsp_url = "rtsp://admin:Imou0588!@192.168.0.103:554/cam/realmonitor?channel=1&subtype=0"
    input_size_value = 23.0  # Kích thước thực tế của QR code (mm)
    target_unit = "mm"
    
    print(f"📷 RTSP URL: {rtsp_url}")
    print(f"📏 Input size value: {input_size_value} {target_unit}")
    print()
    
    # Gọi hàm process_unit_conversion
    result = rtsp_service.process_unit_conversion(rtsp_url, input_size_value)
    
    if result:
        print(f"Result:{result}")
       

def test_with_different_sizes():
    """Test với các kích thước khác nhau"""
    print("\n" + "="*60)
    print("🧪 Test với các kích thước khác nhau...")
    
    rtsp_url = "rtsp://admin:Imou0588!@192.168.1.103:554/cam/realmonitor?channel=1&subtype=0"
    test_sizes = [30.0, 40.0, 50.0, 60.0]  # mm
    
    results = []
    for size in test_sizes:
        print(f"\n📏 Testing với kích thước: {size} mm")
        result = rtsp_service.process_unit_conversion(rtsp_url, size, "mm")
        if result:
            results.append(result)
            print(f"   ✅ Scale factor: {result['scale_factor']:.6f} mm/pixel")
        else:
            print(f"   ❌ Thất bại với kích thước {size} mm")
    
    if results:
        print(f"\n📊 Tổng kết: {len(results)}/{len(test_sizes)} test thành công")
        avg_scale = sum(r['scale_factor'] for r in results) / len(results)
        print(f"🎯 Scale factor trung bình: {avg_scale:.6f} mm/pixel")

def test_error_cases():
    """Test các trường hợp lỗi"""
    print("\n" + "="*60)
    print("⚠️  Test các trường hợp lỗi...")
    
    # Test với URL không hợp lệ
    print("\n🔍 Test với URL không hợp lệ:")
    result = rtsp_service.process_unit_conversion("invalid_url", 50.0)
    if result is None:
        print("   ✅ Xử lý lỗi URL không hợp lệ thành công")
    else:
        print("   ❌ Không xử lý được lỗi URL")
    
    # Test với kích thước âm
    print("\n🔍 Test với kích thước âm:")
    result = rtsp_service.process_unit_conversion("rtsp://test", -10.0)
    if result is None:
        print("   ✅ Xử lý lỗi kích thước âm thành công")
    else:
        print("   ❌ Không xử lý được lỗi kích thước âm")

def main():
    """Hàm chính"""
    print("🧪 Bắt đầu test process_unit_conversion...")
    
    # Test chính
    result = test_process_unit_conversion()
    
    # # Test với các kích thước khác nhau
    # if result:
    #     test_with_different_sizes()
    
    # # Test các trường hợp lỗi
    # test_error_cases()
    
    # print("\n" + "="*60)
    # print("✅ Hoàn thành tất cả test!")

if __name__ == "__main__":
    main() 