import sys
import os
import cv2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.rtsp_service import rtsp_service

def get_test_frame():
    """Lấy một frame từ RTSP để test. Trả về frame hoặc None."""
    rtsp_url = "rtsp://admin:Imou0588!@192.168.0.103:554/cam/realmonitor?channel=1&subtype=0"
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
        detections (list): Danh sách các tuple (rect, name, roi_width, center_x, center_y) từ qr_detection_saveToDb.

    Returns:
        Frame ảnh đã được vẽ.
    """
    output_frame = frame.copy()
    
    if not detections:
        print("⚠️  Không có detection nào để vẽ.")
        return output_frame

    print(f"🎨 Đang vẽ {len(detections)} detection(s) lên frame...")
    for detection in detections:
        # Cấu trúc mới: (rect, name, roi_width, center_x, center_y)
        rect, name, roi_width, center_x, center_y = detection
        
        x_min, y_min, x_max, y_max = rect
        
        # Sử dụng center_x, center_y được trả về từ hàm detection
        center = (center_x, center_y)
        
        # Vẽ hình chữ nhật ROI (màu đỏ)
        cv2.rectangle(output_frame, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
        
        # Vẽ điểm trung tâm (màu vàng)
        cv2.circle(output_frame, center, 8, (0, 255, 255), -1)
        
        # Ghi tên/text và roi_width lên trên ROI
        text = f"{name} @ ({center[0]},{center[1]}) w:{roi_width}"
        cv2.putText(output_frame, text, (x_min, y_min - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Lưu ảnh kết quả
    output_filename = "qr_detection_result_with_centers.jpg"
    cv2.imwrite(output_filename, output_frame)
    print(f"💾 Đã lưu ảnh kết quả: {output_filename}")

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
        print(f"📊 Frame size: {source_frame.shape}")
        
        # 2. Phát hiện QR từ frame đã có
        print("\n🔍 Đang phát hiện QR codes...")
        detected_rois = rtsp_service.qr_detection_saveToDb(source_frame)

        if detected_rois:
            print(f"✅ Phát hiện {len(detected_rois)} QR codes:")
            for i, detection in enumerate(detected_rois):
                rect, name, roi_width, center_x, center_y = detection
                print(f"   QR {i+1}: {name} - Center: ({center_x}, {center_y}) - Width: {roi_width}")
        else:
            print("⚠️ Không phát hiện QR codes nào")

        # 3. Vẽ kết quả lên frame và lưu ảnh
        print("\n🎨 Đang vẽ kết quả lên frame...")
        frame_with_drawings = draw_detections_on_frame(source_frame, detected_rois)
        
        # 4. Lưu thêm một bản copy với tên khác để dễ phân biệt
        output_path = "detection_result_final.jpg"
        cv2.imwrite(output_path, frame_with_drawings)
        
        print(f"✅ Đã lưu kết quả cuối cùng: {os.path.abspath(output_path)}")
        print(f"✅ Đã lưu kết quả với centers: qr_detection_result_with_centers.jpg")

        print("\n✅ Test hoàn thành thành công!")
    else:
        print("❌ Test thất bại vì không thể lấy được frame từ camera hoặc file.")