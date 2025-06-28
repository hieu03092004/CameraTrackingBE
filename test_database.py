#!/usr/bin/env python3
"""
Script test để kiểm tra kết nối database và các chức năng cơ bản
"""

import sys
import os
from datetime import datetime, time
from services.rtsp_service import rtsp_service

# Thêm đường dẫn để import các module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import database_service

def test_database_connection():
    """Test kết nối database"""
    print("🔍 Đang test kết nối database...")
    
    if database_service.connection:
        print("✅ Kết nối database thành công!")
        print(f"   - Host: {database_service.connection.host}")
        print(f"   - Database: {database_service.connection.db.decode()}")
        print(f"   - User: {database_service.connection.user}")
        return True
    else:
        print("❌ Không thể kết nối database!")
        return False





def test_qr_code_operations():
    """Test các thao tác với QR code"""
    print("\n🔍 Đang test thao tác QR code...")
    
    # Test tạo QR code
    qr_code = database_service.create_qr_code(
        name_roi="ROI_Test_1",
        initial_x=100,
        initial_y=200
    )
    
    if qr_code:
        print(f"✅ Đã tạo QR code: {qr_code['name_roi']} (ID: {qr_code['qr_code_id']})")
        
        # Test lấy QR code theo tên
        retrieved_qr = database_service.get_qr_code_by_name("ROI_Test_1")
        if retrieved_qr:
            print(f"✅ Lấy QR code thành công: {retrieved_qr['name_roi']}")
        else:
            print("❌ Không thể lấy QR code theo tên")
            
        return qr_code['qr_code_id']
    else:
        print("❌ Không thể tạo QR code")
        return None

def test_measurement_operations(qr_code_id=None):
    """Test các thao tác với measurement"""
    print("\n🔍 Đang test thao tác measurement...")
    
    # Test tạo measurement
    measurement = database_service.create_measurement(
        x=150,
        y=250,
        qr_code_id=qr_code_id
    )
    
    if measurement:
        print(f"✅ Đã tạo measurement: ({measurement['x']}, {measurement['y']}) (ID: {measurement['measurement_id']})")
        
        if qr_code_id:
            # Test lấy measurements theo QR code
            measurements = database_service.get_measurements_by_qr_code(qr_code_id)
            print(f"✅ Có {len(measurements)} measurements cho QR code {qr_code_id}")
    else:
        print("❌ Không thể tạo measurement")

def test_data_retrieval():
    """Test lấy dữ liệu tổng hợp"""
    print("\n🔍 Đang test lấy dữ liệu tổng hợp...")
    
    # Lấy tất cả cameras
    cameras = database_service.get_all_cameras()
    print(f"✅ Có {len(cameras)} camera(s) trong database")
    
    # Lấy tất cả QR codes
    qr_codes = database_service.get_all_qr_codes()
    print(f"✅ Có {len(qr_codes)} QR code(s) trong database")
    
    # Lấy measurements trong 24h qua
    end_time = datetime.now()
    start_time = datetime(end_time.year, end_time.month, end_time.day - 1, end_time.hour, end_time.minute)
    measurements = database_service.get_measurements_by_time_range(start_time, end_time)
    print(f"✅ Có {len(measurements)} measurement(s) trong 24h qua")

def main():
    # """Hàm chính để chạy tất cả test"""
    # print("🚀 Bắt đầu test database...")
    # print("=" * 50)
    
    # Test kết nối
    if not test_database_connection():
        print("❌ Không thể tiếp tục test vì không kết nối được database")
        return
    
    # Test tạo bảng
    #print(f"Tes{rtsp_service.check_roi_name_exists("ROI_Test_1")}")
    print(f"Test:{database_service.get_active_schedules()}")
    # Test các thao tác cơ bản
 
    # qr_code_id = test_qr_code_operations()
    # test_measurement_operations(qr_code_id)
    
    # # Test lấy dữ liệu
    # test_data_retrieval()
    
    print("\n" + "=" * 50)
    print("✅ Hoàn thành tất cả test database!")

if __name__ == "__main__":
    main() 