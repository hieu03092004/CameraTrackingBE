#!/usr/bin/env python3
"""
Script kiểm tra nhanh chức năng chụp hai camera và lưu frame
"""

import sys
import os
import logging
from datetime import datetime

# Thêm đường dẫn gốc của dự án vào sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.thread_safe_rtsp_service import thread_safe_rtsp_service
from services.database_service import database_service

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def quick_test_dual_camera():
    """
    Kiểm tra nhanh chức năng chụp hai camera
    """
    logger.info("🚀 Bắt đầu kiểm tra nhanh dual camera")
    
    # 1. Kiểm tra database connection
    try:
        cameras = database_service.get_all_cameras()
        if not cameras:
            logger.error("❌ Không có camera nào trong database")
            return
        
        logger.info(f"📱 Tìm thấy {len(cameras)} camera(s) trong database")
        
        # Hiển thị thông tin camera
        for i, camera in enumerate(cameras):
            logger.info(f"   Camera {i+1}: {camera['name']} (ID: {camera['camera_id']})")
            logger.info(f"             RTSP: {camera['rtsp_url']}")
    
    except Exception as e:
        logger.error(f"❌ Lỗi khi kết nối database: {str(e)}")
        return
    
    # 2. Kiểm tra output directory
    output_dir = thread_safe_rtsp_service.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"📁 Tạo thư mục output: {output_dir}")
    else:
        logger.info(f"📁 Thư mục output: {output_dir}")
    
    # 3. Kiểm tra từng camera một cách tuần tự
    test_cameras = cameras[:2]  # Chỉ test 2 camera đầu tiên
    
    results = []
    for i, camera in enumerate(test_cameras):
        logger.info(f"\n📸 Kiểm tra Camera {i+1}: {camera['name']}")
        
        try:
            # Lấy frame
            frame = thread_safe_rtsp_service.get_frame_from_rtsp(camera['rtsp_url'])
            
            if frame is not None:
                logger.info(f"✅ Frame lấy thành công từ {camera['name']}")
                
                # Phát hiện QR codes
                qr_codes = thread_safe_rtsp_service.qr_detection_saveToDb_safe(frame, camera['camera_id'])
                
                # Lưu frame debug
                debug_file = thread_safe_rtsp_service.save_frame_for_debug(
                    frame, camera['camera_id'], f"Test-{i+1}", qr_codes
                )
                
                results.append({
                    'camera_name': camera['name'],
                    'camera_id': camera['camera_id'],
                    'success': True,
                    'qr_count': len(qr_codes) if qr_codes else 0,
                    'debug_file': debug_file
                })
                
                logger.info(f"🎯 Phát hiện {len(qr_codes) if qr_codes else 0} QR codes")
                if debug_file:
                    logger.info(f"💾 Debug file: {debug_file}")
                
            else:
                logger.error(f"❌ Không thể lấy frame từ {camera['name']}")
                results.append({
                    'camera_name': camera['name'],
                    'camera_id': camera['camera_id'],
                    'success': False,
                    'error': 'Failed to get frame'
                })
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi kiểm tra {camera['name']}: {str(e)}")
            results.append({
                'camera_name': camera['name'],
                'camera_id': camera['camera_id'],
                'success': False,
                'error': str(e)
            })
    
    # 4. Tổng kết kết quả
    logger.info("\n" + "="*60)
    logger.info("📊 KẾT QUẢ KIỂM TRA")
    logger.info("="*60)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    logger.info(f"✅ Thành công: {len(successful_tests)}/{len(results)} camera(s)")
    logger.info(f"❌ Thất bại: {len(failed_tests)}/{len(results)} camera(s)")
    
    if successful_tests:
        logger.info(f"\n✅ Camera thành công:")
        for result in successful_tests:
            logger.info(f"   📷 {result['camera_name']} (ID: {result['camera_id']})")
            logger.info(f"      🎯 QR codes: {result['qr_count']}")
            if result.get('debug_file'):
                logger.info(f"      📸 Debug file: {result['debug_file']}")
    
    if failed_tests:
        logger.info(f"\n❌ Camera thất bại:")
        for result in failed_tests:
            logger.info(f"   📷 {result['camera_name']} (ID: {result['camera_id']})")
            logger.info(f"      ❌ Lỗi: {result['error']}")
    
    logger.info(f"\n📁 Kiểm tra thư mục output để xem các file debug: {output_dir}")
    logger.info("="*60)

if __name__ == "__main__":
    try:
        quick_test_dual_camera()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test đã bị dừng bởi người dùng")
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn: {str(e)}")
