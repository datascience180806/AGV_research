# Báo cáo Đánh giá Năng lực Chẩn đoán Sự cố AI (AI Anomaly Detection & Diagnosis Benchmark Report)

Hệ thống đánh giá hiệu năng suy luận và chẩn đoán sự cố của các mô hình AI thông qua giám sát luồng gói tin trạng thái VDA 5050 và dữ liệu cảm biến (telemetry stream) trong môi trường nhà máy giả lập.

---

## 1. Cơ chế vận hành & Giả lập cảm biến

Hệ thống được thiết kế theo hướng **xác định (deterministic)** về mặt vận hành để đảm bảo xe AGV luôn di chuyển thành công 100% không va chạm thông qua thuật toán định tuyến A* hard-coded. Từ đó, AI tập trung hoàn toàn vào việc đọc và phân tích luồng dữ liệu cảm biến được phát ra để nhận diện sự cố.

### Các loại cảm biến giả lập (Sensor Streams):
* **Weight Sensor (Cân nặng)**: Trọng lượng hàng hóa thực tế và cảnh báo quá tải trọng (`overload_warning`).
* **LiDAR Scanner (Khoảng cách)**: Quét vật cản tĩnh và động, cảnh báo suy giảm chất lượng quét (`scan_quality`).
* **Temperature Monitor (Nhiệt độ)**: Giám sát nhiệt độ động cơ trái/phải và pin, cảnh báo quá nhiệt (`motor_warning_threshold_c`).
* **Encoder Sensor (Vận tốc/Hành trình)**: RPM bánh xe, đo tốc độ thực tế (MPS) và odometer tích lũy.
* **Battery Monitor (Trạng thái pin)**: Điện áp, dòng điện tải, tỷ lệ tiêu hao (%/phút), và tình trạng sức khỏe của từng cell pin (`cell_health`).

---

## 2. Các Cấp Độ Kịch Bản Chẩn Đoán (Scenarios Levels)

Hệ thống benchmark mới bao gồm 5 cấp độ khó tăng dần:
* **Level 1 (Single Fault)**: 1 lỗi đơn lẻ, dấu hiệu rõ ràng (Rò rỉ pin, Quá tải trọng, LiDAR bị che, Động cơ quá nhiệt).
* **Level 2 (Multi Fault)**: Nhiều sự cố độc lập xảy ra đồng thời trên các xe khác nhau.
* **Level 3 (Cascading Fault)**: Sự cố dây chuyền (ví dụ: Quá tải trọng -> Phanh mòn -> Va chạm vật lý).
* **Level 4 (Subtle Fault)**: Lỗi tinh vi, diễn biến chậm (Drift cảm biến cân nặng, Cell pin yếu đột ngột).
* **Level 5 (Real-world)**: Mô phỏng toàn bộ hoạt động của nhà máy với hàng chục xe và lỗi phát sinh liên tục.

---

## 3. Bản đồ nhà máy mới: `multi_zone_factory`

Bản đồ có kích thước **120m x 100m** gồm 10 điểm trạm (Node) với các vùng sạc nhanh, vùng hạn chế di chuyển (Restricted Zone) và các chướng ngại vật tĩnh (Tường ngăn và cột trụ).

---

## 4. Kết quả Đánh giá Benchmark (Benchmark Results)

### Level 1 - Scenario 101 (Battery Leak Detection During Transport)
* **Mô tả**: Xe `AGV_02` (chở tải trọng nặng 140kg) bị cấy lỗi rò rỉ pin đột ngột (`battery_leak`) tại giây thứ **15.0**, làm tốc độ hao pin tăng gấp **8 lần** bình thường. AI cần phát hiện sớm qua telemetry trước khi xe cạn pin hoàn toàn tại giây thứ 45.

| Chỉ số đo lường (Metrics) | Gemini 2.5 Flash |
| :--- | :---: |
| **Trạng thái Chẩn đoán** | **SUCCESS** |
| **Độ chính xác nhận biết (Detection Accuracy)** | **100.0%** |
| **Thời gian phát hiện sớm (Detection Latency)** | **30.0 giây** |
| **Phân tích nguyên nhân gốc đúng (Correct Root Cause)** | **ĐÚNG (True)** |
| **Số cảnh báo sai (False Positives)** | **0** |
| **Dung lượng pin còn lại cuối cùng (AGV_01 / AGV_02)** | **89.5% / 0.0%** |
| **Thời gian giả lập (Simulation Time)** | **120.0 giây** |

### Ghi chú phân tích chẩn đoán của Gemini 2.5 Flash:
1. **Phát hiện Anomaly**: Mô hình nhận diện chính xác sự sụt giảm bất thường về dung lượng pin của `AGV_02` từ 85% xuống thấp một cách nhanh chóng khi đang chở hàng nặng.
2. **Khuyến nghị hành động (Recommended Actions)**: Đề xuất chuyển hướng xe `AGV_02` về trạm sạc gần nhất `CHARGING_2` và lập lịch bảo trì cho khối pin bị lỗi.
3. **Độ trễ API**: Do giới hạn cuộc gọi API của gói miễn phí (Rate Limit 15 RPM), chu kỳ chẩn đoán được thiết lập ở mức **15 giây/lần** để đảm bảo quá trình chạy kiểm tra diễn ra ổn định và thành công.