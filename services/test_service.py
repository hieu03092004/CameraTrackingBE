import sys
import os
import cv2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.rtsp_service import rtsp_service

def get_test_frame():
    """Lấy một frame từ RTSP để test. Trả về frame hoặc None."""
    rtsp_url = "rtsp://admin:Imou0588!@192.168.1.103:554/cam/realmonitor?channel=1&subtype=0"
    print(f"Đang thử kết nối đến: {rtsp_url}")
    
    frame = rtsp_service.get_frame_from_rtsp(rtsp_url)
    
    if frame is not None:
        print("✅ Lấy frame thành công!")
        return frame
    else:
        print("❌ Không thể lấy frame từ RTSP stream.")
        return None

def draw_detections_on_frame(frame, detections):
    """
    Vẽ các vùng ROI và điểm trung tâm lên frame.
    
    Args:
        frame: Frame ảnh gốc.
        detections (list): Danh sách các dictionary detection từ qr_detection.

    Returns:
        Frame ảnh đã được vẽ.
    """
    output_frame = frame.copy()
    
    if not detections:
        print("⚠️  Không có detection nào để vẽ.")
        return output_frame

    print(f"🎨 Đang vẽ {len(detections)} detection(s) lên frame...")
    for detection in detections:
        rect = detection['rect']
        center = detection['center']
        name = detection['name']
        
        x_min, y_min, x_max, y_max = rect
        
        # Vẽ hình chữ nhật ROI (màu đỏ)
        cv2.rectangle(output_frame, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
        
        # Vẽ điểm trung tâm (màu vàng)
        cv2.circle(output_frame, center, 8, (0, 255, 255), -1)
        
        # Ghi tên/text lên trên ROI
        cv2.putText(output_frame, f"{name} @ ({center[0]},{center[1]})", (x_min, y_min - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    return output_frame

if __name__ == "__main__":
    print("🚀 Bắt đầu test: Lấy frame, phát hiện QR, và vẽ kết quả.")

    # 1. Lấy frame từ camera
    source_frame = get_test_frame()

    # Nếu không lấy được frame từ camera, thử đọc từ file dự phòng
    if source_frame is None:
        image_path = "test_frame.jpg"
        print(f"\n🔄 Thử đọc frame từ file dự phòng: {image_path}")
        if os.path.exists(image_path):
            source_frame = cv2.imread(image_path)
            if source_frame is not None:
                print("✅ Đọc frame từ file thành công.")
        else:
            print(f"❌ Không tìm thấy file ảnh dự phòng: {image_path}")

    if source_frame is not None:
        # 2. Phát hiện QR từ frame đã có
        detected_rois = rtsp_service.qr_detection(source_frame)

        # 3. Vẽ kết quả lên frame (nếu có gì để vẽ)
        frame_with_drawings = draw_detections_on_frame(source_frame, detected_rois)
        
        # 4. Lưu file ảnh kết quả
        output_path = "detection_result.jpg"
        cv2.imwrite(output_path, frame_with_drawings)
        
        print(f"✅ Đã vẽ và lưu kết quả vào file: {os.path.abspath(output_path)}")

        if detected_rois:
            print("✅ Test hoàn thành thành công!")
        else:
            print("⚠️  Test hoàn thành nhưng không phát hiện được QR code nào.")
    else:
        print("❌ Test thất bại vì không thể lấy được frame từ camera hoặc file.")