# Cơ chế vận hành

## Mô tả về xe AGV
Hệ thống sử dụng các xe tự hành AGV (Automated Guided Vehicle) tuân thủ tiêu chuẩn giao thức công nghiệp **VDA 5050**. Mỗi xe có các đặc tính vận hành sau:
* **Khả năng di chuyển**: Xe di chuyển trên sơ đồ lưới nhà kho hai chiều (2D Grid Map) kết nối bởi hệ thống các Node (điểm trạm) và Edge (đường dẫn nối giữa các trạm). Xe di chuyển dọc theo các Edge bằng đường thẳng nối tiếp nhau giữa các Node.
* **Hệ thống Pin (Battery)**: Pin tiêu thụ năng lượng liên tục trong quá trình di chuyển và thực hiện các tác vụ xử lý hàng hóa. Khi mức pin giảm xuống dưới ngưỡng an toàn, xe cần được điều động đến các Node nằm trong Vùng sạc pin (`CHARGING_ZONE`) để kích hoạt hành động sạc (`charge`). Nếu pin về mức 0%, xe sẽ lập tức dừng hoạt động và kịch bản thử nghiệm bị đánh giá thất bại (`battery_dead`).
* **Hệ thống tác vụ (Actions)**: Xe hỗ trợ thực thi các tác vụ tại các Node như: lấy hàng (`pickUp`), dỡ hàng (`dropOff`), sạc điện (`charge`). Các tác vụ này có tính chất ngăn chặn cứng (`HARD blockingType`), nghĩa là xe phải đứng yên tại Node cho đến khi hoàn thành xong tác vụ mới được đi tiếp.

## Mô tả về trung tâm điều phối
Trung tâm điều phối đóng vai trò là "Bộ não điều khiển tối cao" (Master Control) quản lý và giám sát toàn bộ hạm đội xe AGV:
* **Thu thập dữ liệu**: Tiếp nhận trạng thái hiện tại của từng xe (vị trí tọa độ thực tế, dung lượng pin còn lại, các tác vụ đang thực thi) và thông tin về các Yêu cầu vận chuyển (`transport_requests`).
* **Lập kế hoạch lộ trình (Path Routing)**: Tính toán đường đi tối ưu cho từng xe dựa trên sơ đồ mặt bằng (`factory_layout`), tránh va chạm với các vật cản tĩnh (`obstacles`) và hạn chế chồng chéo lộ trình giữa các xe ở các giao lộ để ngăn ngừa tai nạn hoặc tắc nghẽn (`deadlock`).
* **Sinh chỉ thị VDA 5050**: Đóng gói lộ trình di chuyển thành các đơn hàng tiêu chuẩn (`VDA 5050 Orders`) để truyền trực tiếp đến các xe AGV.

## Cơ chế truyền tin giữa AGV và trung tâm điều phối
Quy trình trao đổi dữ liệu tuân thủ nghiêm ngặt chuẩn **VDA 5050**:
1. **Trạng thái xe (State Message)**: Xe AGV định kỳ gửi gói tin trạng thái lên hệ thống để thông báo vị trí, mức pin hiện tại, và trạng thái các hành động đang chờ hoặc đang thực thi (`actionStates`).
2. **Yêu cầu chỉ lệnh (Order Message)**: Trung tâm điều phối gửi các gói tin chỉ thị chứa danh sách các Node và Edge liên kết cần di chuyển qua. Các Node và Edge được sắp xếp xen kẽ và đánh số thứ tự tuần tự tăng dần (`sequenceId`).
3. **Cập nhật tác vụ (Action Updates)**: Khi đi đến đúng Node yêu cầu, xe AGV sẽ tự động kích hoạt tác vụ đính kèm, cập nhật trạng thái tác vụ từ `WAITING` sang `RUNNING` và kết thúc bằng `FINISHED` để thông báo cho Trung tâm điều phối.

---

# Scenarios

## Scenario 1: Level 1 basic
* **Mô tả**: Kịch bản cơ bản nhất gồm 1 xe AGV thực hiện vận chuyển đơn lẻ. Xe phải di chuyển từ vị trí xuất phát để nhận kiện hàng tại điểm lấy hàng và chuyển giao tới điểm đích được chỉ định trên sơ đồ phẳng không có vật cản phức tạp.
* **Kỳ vọng**: Xe đi đúng hành trình ngắn nhất, thực hiện đúng các tác vụ lấy hàng/dỡ hàng tuần tự, dừng lại chính xác tại điểm đích và hoàn thành nhiệm vụ an toàn.

## Scenario 2: Level 2 intermediate
* **Mô tả**: Kịch bản tăng độ khó bằng cách bổ sung thêm vật cản tĩnh (`obstacles`) nằm trực diện trên đường nối trực tiếp giữa các điểm trạm, hoặc xe xuất phát với mức pin yếu buộc hệ thống phải tự đưa ra quyết định di chuyển đi sạc trước khi thực hiện đơn hàng.
* **Kỳ vọng**: Xe biết đi đường vòng qua các lối đi thay thế để tránh đâm vào vật cản trung tâm, hoặc chủ động ghé qua trạm sạc điện cho đến khi mức pin an toàn rồi mới tiếp tục đi lấy hàng.

## Scenario 3: Level 3 advanced
* **Mô tả**: Kịch bản điều phối đa xe (2 xe AGV trở lên) hoạt động đồng thời. Lộ trình di chuyển của các xe có các điểm giao cắt hoặc đi ngược chiều nhau trên các hành lang hẹp, tạo ra rủi ro va chạm trực tiếp.
* **Kỳ vọng**: Trung tâm điều phối phải tính toán giãn cách thời gian di chuyển hoặc điều hướng một xe đi đường tránh để nhường đường cho xe còn lại, đảm bảo không xảy ra va chạm giữa các xe.

## Scenario 4: Level 4 expert
* **Mô tả**: Kịch bản phức tạp nhất gồm nhiều xe vận hành đồng thời trong không gian hẹp với mật độ yêu cầu vận chuyển dày đặc, dễ xảy ra tình trạng khóa lẫn nhau (Deadlock).
* **Kỳ vọng**: Mô hình phải tối ưu hóa thứ tự ưu tiên của các xe, phân luồng giao thông động thông minh để giải quyết deadlock và hoàn thành toàn bộ yêu cầu vận chuyển trong thời gian tối thiểu.

---

# Layout 1: Simple warehouse

## Mô tả:
Bản đồ **`simple_warehouse`** có kích thước thực tế là **60m x 50m**. Bản đồ gồm 6 điểm trạm chủ chốt (`DOCK_A`, `DOCK_B`, `WP_1`, `WP_2`, `SHELF_B1`, `SHELF_B2`) nối với nhau qua các đường hành lang bao quanh. Ở chính giữa bản đồ có một bức tường lớn cản đường (`WALL_CENTER` tọa độ từ x=15 đến 35, y=15 đến 25) và một cột trụ tròn lớn (`PILLAR_1` tâm x=50, y=20, bán kính 2m). Bản đồ có một vùng sạc pin nhanh (`CHARGING_ZONE`) nằm ở góc dưới bên trái.

![Simple Warehouse Layout](images/simple_warehouse_layout.png)

---

## Scenario 1 (Single AGV - Simple Pickup and Delivery)
**Yêu cầu**: Xe `AGV_01` (xuất phát từ `DOCK_A`) cần lấy hàng tại `DOCK_A` và giao đến `SHELF_B1`.

| Metric / Model | Gemini 2.5 Flash | Qwen Max (Cloud) | Llama 3.3 70B (Groq) | GPT-OSS 20B (Groq) | Llama 3.1 8B (Groq) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Trạng thái chạy** | **SUCCESS** | **SUCCESS** | **SUCCESS** | **FAILED** | **FAILED** |
| **Độ trễ API (ms)** | ~7587.9 | ~6417.5 | ~1491.3 | ~1602.8 | ~1523.0 |
| **Thời gian mô phỏng (s)**| 35.45 | 35.45 | 35.45 | 0.00 | 48.75 |
| **Số vụ va chạm** | 0 | 0 | 0 | 0 | 1 |
| **Pin còn lại (%)** | 92.9% | 93.3% | 92.9% | 0.00% | 6.46% |

### Ghi chú lỗi (Notes on Failed Models):
* **GPT-OSS 20B (Groq)**: Thất bại do lỗi cấu trúc chỉ thị (`invalid_order`). Mô hình trả về kết quả JSON bị chèn các phần tử rỗng `""` xen kẽ trong danh sách `nodes` và `edges`, khiến hệ thống không thể phân tích cú pháp để đưa vào giả lập (Gây lỗi `'str' object has no attribute 'get'`).
* **Llama 3.1 8B (Groq)**: Thất bại do lỗi va chạm (`collision`). Mô hình suy luận kém, tự sinh thêm lộ trình vòng qua `DOCK_B` và đi chéo xuyên thẳng qua bức tường trung tâm `WALL_CENTER`.

---

## Scenario 2 (Single AGV - Sequential Deliveries)
**Yêu cầu**: Xe `AGV_01` thực hiện liên tiếp 2 đơn hàng: Nhận hàng tại `DOCK_A` giao tới `SHELF_B1`, sau đó nhận hàng tại `DOCK_B` giao tới `SHELF_B2`.

| Metric / Model | Gemini 2.5 Flash | Qwen Max (Cloud) | Llama 3.3 70B (Groq) | GPT-OSS 20B (Groq) | Llama 3.1 8B (Groq) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Trạng thái chạy** | **SUCCESS** | **SUCCESS** | **SUCCESS** | **FAILED** | **FAILED** |
| **Độ trễ API (ms)** | ~11138.9 | ~6201.5 | ~1850.0 | - | - |
| **Thời gian mô phỏng (s)**| 35.45 | 35.45 | 35.45 | - | - |
| **Số vụ va chạm** | 0 | 0 | 0 | - | - |
| **Pin còn lại (%)** | 92.9% | 93.3% | 92.9% | - | - |

### Ghi chú lỗi (Notes on Failed Models):
* **GPT-OSS 20B (Groq)**: Thất bại do lỗi cấu trúc JSON không hợp lệ.
* **Llama 3.1 8B (Groq)**: Thất bại do va chạm. Lộ trình di chuyển sinh ra đi chéo đâm qua góc tường trung tâm.

---

## Scenario 3 (Single AGV - Obstacle Avoidance)
**Yêu cầu**: Xe `AGV_01` cần nhận hàng tại `DOCK_A` và chuyển đến `DOCK_B` trong điều kiện có bức tường `WALL_CENTER` chắn đường trực tiếp.

| Metric / Model | Gemini 2.5 Flash | Qwen Max (Cloud) | Llama 3.3 70B (Groq) | GPT-OSS 20B (Groq) | Llama 3.1 8B (Groq) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Trạng thái chạy** | **FAILED** | **FAILED** | **FAILED** | **FAILED** | **FAILED** |
| **Độ trễ API (ms)** | ~13744.2 | ~13384.8 | ~2100.0 | - | - |
| **Thời gian mô phỏng (s)**| 90.00 (Timeout) | 19.70 | 45.10 | - | - |
| **Số vụ va chạm** | 0 | 1 | 1 | - | - |
| **Pin còn lại (%)** | 82.06% | 96.08% | 42.10% | - | - |

### Ghi chú lỗi (Notes on Failed Models):
* **Gemini 2.5 Flash**: Thất bại do quá thời gian kịch bản (`timeout`). Lộ trình lập đúng đi vòng qua vật cản trung tâm và pin hoàn toàn khỏe mạnh (còn 82%), tuy nhiên do mô hình sinh quá nhiều Node/Edge dư thừa lặp lại khiến xe di chuyển lòng vòng không dừng trước khi hết 90 giây giới hạn kịch bản.
* **Qwen Max (Cloud)**: Thất bại do va chạm (`collision`). Tương tự như Llama 3.3 70B, mô hình cố gắng lập lộ trình đi thẳng cắt qua rìa của `WALL_CENTER` dẫn đến đâm vào vật cản ở giây thứ 19.70.
* **Llama 3.3 70B (Groq)**: Thất bại do va chạm (`collision`). Mô hình cố gắng cắt góc đi sát ranh giới của `WALL_CENTER` dẫn đến va chạm.
* **GPT-OSS 20B (Groq)**: Thất bại do lỗi sinh cấu trúc lộ trình VDA 5050.
* **Llama 3.1 8B (Groq)**: Thất bại do va chạm với bức tường trung tâm.

---

## Scenario 4 (Single AGV - Low Battery Charging)
**Yêu cầu**: Xe `AGV_01` xuất phát với mức pin thấp, cần tự tính toán ghé vào `CHARGING_ZONE` để sạc pin trước khi thực hiện đơn hàng giao từ `DOCK_B` đến `SHELF_B1`.

| Metric / Model | Gemini 2.5 Flash | Qwen Max (Cloud) | Llama 3.3 70B (Groq) | GPT-OSS 20B (Groq) | Llama 3.1 8B (Groq) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Trạng thái chạy** | **SUCCESS** | **FAILED** | **FAILED** | **FAILED** | **FAILED** |
| **Độ trễ API (ms)** | ~16299.5 | ~9327.4 | ~2500.0 | - | - |
| **Thời gian mô phỏng (s)**| 77.15 | 36.40 | 6.20 | - | - |
| **Số vụ va chạm** | 0 | 1 | 0 | - | - |
| **Pin còn lại (%)** | 25.03% | 32.75% | 0.00% | - | - |

### Ghi chú lỗi (Notes on Failed Models):
* **Qwen Max (Cloud)**: Thất bại do va chạm (`collision`). Mô hình lập đúng hành trình sạc pin, tuy nhiên khi di chuyển từ trạm sạc về điểm đích đã bị đâm nhẹ vào rìa vùng cản.
* **Llama 3.3 70B (Groq)**: Thất bại do cạn pin giữa đường. Mô hình chưa tối ưu hóa việc điều phối ghé trạm sạc kịp thời hoặc lộ trình sinh ra quá dài.
* **GPT-OSS 20B & Llama 3.1 8B**: Thất bại do lỗi sinh cấu trúc chỉ thị không hợp lệ.

# Các mục tiêu tiếp theo
- Thử nghiệm thêm các models có lượng tham số lớn hơn
- Thử nghiệm thêm các layout có độ khó cao hơn
- Thử nghiệm thêm các scenario có độ khó cao hơn
- Sử dụng các biện pháp để dùng chung cho các APIs, tránh phải viết adapter cho từng cái
- Tiềm kiếm và thử nghiệm được các cases xuất hiện trong thực tế
