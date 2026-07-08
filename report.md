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

## Thông số động học và tiêu hao pin

Để phục vụ việc lập lộ trình và tính toán năng lượng, dưới đây là các thông số động học chi tiết của xe AGV trong hệ thống giả lập:
* **Tần số cập nhật (Tick Rate)**: Mô phỏng chạy ở tần số **20Hz** (20 ticks tương đương 1 giây thực tế).
* **Tốc độ di chuyển của xe ($v$)**: Mỗi tick xe di chuyển được quãng đường cố định là `0.06 mét` (cấu hình `speed: 0.06` trong kịch bản).
  $$v = 0.06 \text{ m/tick} \times 20 \text{ ticks/s} = 1.2 \text{ m/s} \text{ (tương đương } 4.32 \text{ km/h)}$$
* **Hao hụt pin khi di chuyển (Driving Drainage)**: Tiêu hao **`0.01%` dung lượng pin trên mỗi tick** di chuyển (tương đương **`0.2%` trên mỗi giây** thực tế).
* **Hao hụt pin khi đứng yên (Idle Drainage)**: Tiêu hao **`0.001%` dung lượng pin trên mỗi tick** đứng chờ (tương đương **`0.02%` trên mỗi giây** thực tế).

### Ví dụ tính toán thực tế trên sơ đồ:

#### Ví dụ 1: Đi từ `DOCK_B` đến `DOCK_A`
* **Khoảng cách ($S$)**: Tọa độ `DOCK_B` $(5.0, 35.0)$ và `DOCK_A` $(5.0, 5.0)$ có độ lệch trục Y là:
  $$S = 35.0 - 5.0 = 30 \text{ mét}$$
* **Thời gian di chuyển ($t$)**:
  $$t = \frac{30 \text{ m}}{1.2 \text{ m/s}} = 25 \text{ giây}$$
* **Số tick mô phỏng**:
  $$\text{ticks} = 25 \text{ s} \times 20 \text{ ticks/s} = 500 \text{ ticks}$$
* **Pin tiêu thụ**:
  $$\text{Pin hao hụt} = 500 \text{ ticks} \times 0.01\%/\text{tick} = 5.0\%$$
  *(Hoặc: $25 \text{ giây} \times 0.2\%/\text{giây} = 5.0\%$)*

#### Ví dụ 2: Đi từ `DOCK_B` đến `SHELF_B2`
* **Khoảng cách ($S$)**: Tọa độ `DOCK_B` $(5.0, 35.0)$ và `SHELF_B2` $(45.0, 35.0)$ có độ lệch trục X là:
  $$S = 45.0 - 5.0 = 40 \text{ mét}$$
* **Thời gian di chuyển ($t$)**:
  $$t = \frac{40 \text{ m}}{1.2 \text{ m/s}} \approx 33.33 \text{ giây}$$
* **Số tick mô phỏng**:
  $$\text{ticks} = 33.33 \text{ s} \times 20 \text{ ticks/s} \approx 667 \text{ ticks}$$
* **Pin tiêu thụ**:
  $$\text{Pin hao hụt} = 667 \text{ ticks} \times 0.01\%/\text{tick} \approx 6.67\%$$
  *(Hoặc: $33.33 \text{ giây} \times 0.2\%/\text{giây} = 6.67\%$)*

---

# Các Cấp Độ Kịch Bản (Scenarios Levels)

## Level 1: Basic
* **Scenario 001 (Simple Pickup and Delivery)**: 1 xe AGV di chuyển từ vị trí xuất phát để nhận kiện hàng tại điểm lấy hàng và chuyển giao tới điểm đích trên sơ đồ phẳng không có vật cản phức tạp. Pin xe khởi điểm ở mức cao (100%).
* **Scenario 002 (Sequential Deliveries)**: 1 xe AGV thực hiện chuỗi nhiều đơn hàng nhận và giao tuần tự qua các trạm khác nhau trên sơ đồ trống để thử nghiệm khả năng duy trì trạng thái hàng đợi chỉ thị của model.

## Level 2: Intermediate
* **Scenario 010 (Obstacle Avoidance)**: 1 xe AGV cần di chuyển qua khu vực có chứa vật cản tĩnh lớn nằm chắn trực diện trên lối đi để kiểm thử khả năng tìm đường vòng tránh của mô hình.
* **Scenario 012 (Low Battery Charging)**: 1 xe AGV xuất phát với mức pin yếu (40%), bắt buộc mô hình phải tự nhận biết dung lượng pin để điều hướng xe đến vùng sạc pin trước khi thực hiện đơn hàng.
* **Scenario 013 (Low Battery Sustainable Charging)**: 1 xe AGV xuất phát từ `DOCK_B` với lượng pin tối thiểu (5.5%) và mục tiêu là giao hàng tới `SHELF_B2`. AI phải nhận biết được mức pin khứ hồi để điều hướng xe về trạm sạc `DOCK_A` trước khi thực hiện nhiệm vụ, đảm bảo xe đủ pin quay lại trạm sạc sau khi hoàn thành.

## Level 3: Advanced
* **Scenario 020 (Multi-AGV Junction Conflict)**: Điều phối từ 2 xe AGV hoạt động đồng thời ngược chiều nhau trên các đoạn đường hẹp, bắt buộc mô hình phải tính toán thời gian hoặc đổi hướng một xe để tránh va chạm chéo tại giao lộ.

## Level 4: Expert
* **Scenario 030 (Multi-AGV Deadlock Resolution)**: Nhiều xe vận hành đồng thời trong không gian hẹp với mật độ yêu cầu dày đặc, đòi hỏi mô hình phải lập lộ trình phân luồng khôn ngoan để giải quyết nguy cơ kẹt xe (deadlock).

---

# Layout 1: Simple warehouse

## Mô tả:
Bản đồ **`simple_warehouse`** có kích thước thực tế là **60m x 50m**. Bản đồ gồm 6 điểm trạm chủ chốt (`DOCK_A`, `DOCK_B`, `WP_1`, `WP_2`, `SHELF_B1`, `SHELF_B2`) nối với nhau qua các đường hành lang bao quanh. Ở chính giữa bản đồ có một bức tường lớn cản đường (`WALL_CENTER` tọa độ từ x=15 đến 35, y=15 đến 25) và một cột trụ tròn lớn (`PILLAR_1` tâm x=50, y=20, bán kính 2m). Bản đồ có một vùng sạc pin nhanh (`CHARGING_ZONE`) nằm ở góc dưới bên trái.

![Simple Warehouse Layout](images/simple_warehouse_layout.png)

---

## Level 1 - Scenario 001 (Simple Pickup and Delivery)
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

## Level 1 - Scenario 002 (Sequential Deliveries)
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

## Level 2 - Scenario 010 (Obstacle Avoidance)
**Yêu cầu**: Xe `AGV_01` cần nhận hàng tại `DOCK_A` và chuyển đến `DOCK_B` trong điều kiện có bức tường `WALL_CENTER` chắn đường trực tiếp (Pin khởi điểm 100%).

| Metric / Model | Gemini 2.5 Flash | Qwen Max (Cloud) | Llama 3.3 70B (Groq) | GPT-OSS 20B (Groq) | Llama 3.1 8B (Groq) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Trạng thái chạy** | **FAILED** | **FAILED** | **FAILED** | **FAILED** | **FAILED** |
| **Độ trễ API (ms)** | ~13744.2 | ~13384.8 | ~2100.0 | - | - |
| **Thời gian mô phỏng (s)**| 90.00 (Timeout) | 19.70 | 45.10 | - | - |
| **Số vụ va chạm** | 0 | 1 | 1 | - | - |
| **Pin còn lại (%)** | 82.06% | 96.08% | 42.10% | - | - |

### Ghi chú lỗi (Notes on Failed Models):
* **Gemini 2.5 Flash**: Thất bại do quá thời gian kịch bản (`timeout`). Lộ trình lập đúng đi vòng qua vật cản trung tâm và pin hoàn toàn khỏe mạnh (còn 82%), tuy nhiên do mô hình sinh quá nhiều Node/Edge dư thừa lặp lại khiến xe di chuyển lòng vòng không dừng trước khi hết 90 giây giới hạn kịch bản.
* **Qwen Max (Cloud)**: Thất bại do va chạm (`collision`). Mô hình cố gắng lập lộ trình đi thẳng cắt qua rìa của `WALL_CENTER` dẫn đến đâm vào vật cản ở giây thứ 19.70.
* **Llama 3.3 70B (Groq)**: Thất bại do va chạm (`collision`). Mô hình cố gắng cắt góc đi sát ranh giới của `WALL_CENTER` dẫn đến va chạm.
* **GPT-OSS 20B (Groq)**: Thất bại do lỗi sinh cấu trúc lộ trình VDA 5050.
* **Llama 3.1 8B (Groq)**: Thất bại do va chạm với bức tường trung tâm.

---

## Level 2 - Scenario 012 (Low Battery Charging)
**Yêu cầu**: Xe `AGV_01` xuất phát với mức pin thấp (40%), cần tự tính toán ghé vào `CHARGING_ZONE` để sạc pin trước khi thực hiện đơn hàng giao từ `DOCK_B` đến `SHELF_B1`.

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

---

## Level 2 - Scenario 013 (Low Battery Sustainable Charging)
**Yêu cầu**: Xe `AGV_01` ở `DOCK_B` có pin cực thấp (5.5%), cần sạc tại `DOCK_A` trước khi giao hàng tới `SHELF_B2`.

| Metric / Model | Gemini 2.5 Flash | Qwen Max (Cloud) | Llama 3.3 70B (Groq) |
| :--- | :---: | :---: | :---: |
| **Trạng thái chạy** | **SUCCESS** | **FAILED** | **FAILED** |
| **Độ trễ API (ms)** | ~19328.2 | ~6601.1 | ~2179.1 |
| **Thời gian mô phỏng (s)**| 89.40 | 29.60 | 29.60 |
| **Số vụ va chạm** | 0 | 0 | 0 |
| **Pin còn lại (%)** | 88.36% | 0.00% | 0.00% |

### Ghi chú lỗi (Notes on Failed Models):
* **Qwen Max (Cloud)**: Thất bại do lỗi cạn pin (`battery_dead`). Mô hình lập lộ trình đi thẳng từ `DOCK_B` đến `SHELF_B2` mà không lập lộ trình đi sạc trước, làm xe hết pin và dừng lại ở `WP_2`.
* **Llama 3.3 70B (Groq)**: Thất bại tương tự do cố đi thẳng mà không sạc, gây sập nguồn tại `WP_2`.
* **Gemini 2.5 Flash (Thành công)**: Đã giải bài toán xuất sắc. Mô hình tự lên kế hoạch cho xe di chuyển từ `DOCK_B` về `DOCK_A` để sạc pin (về tới nơi còn `0.46%` pin), sạc đầy lên `100%`, sau đó quay lại lấy hàng tại `DOCK_B` và giao tới `SHELF_B2` thành công mỹ mãn.

---

## Level 3 - Scenario 020 (Multi-AGV Junction Conflict)
**Yêu cầu**: Điều phối 2 xe AGV tránh đụng nhau tại giao lộ. Xe `AGV_01` giao hàng từ `DOCK_A` đến `SHELF_B2`. Xe `AGV_02` giao hàng từ `SHELF_B2` đến `DOCK_A`. Lộ trình đi chéo của hai xe giao cắt trực tiếp tại khu vực hành lang hẹp trung tâm.

| Metric / Model | Gemini 2.5 Flash | Qwen Max (Cloud) | Llama 3.3 70B (Groq) |
| :--- | :---: | :---: | :---: |
| **Trạng thái chạy** | **SUCCESS** | **SUCCESS** | **SUCCESS** |
| **Độ trễ API (ms)** | ~17845.8 | ~14678.0 | ~2430.0 |
| **Thời gian mô phỏng (s)**| 60.45 | 60.45 | 60.45 |
| **Số vụ va chạm** | 0 | 0 | 0 |
| **Pin AGV_01 (%)** | 78.36% | 78.36% | 78.36% |
| **Pin AGV_02 (%)** | 73.36% | 73.36% | 73.36% |

### Ghi chú phân tích kịch bản:
* Cả 3 mô hình lớn **Gemini 2.5 Flash**, **Qwen Max** và **Llama 3.3 70B** đều hoàn thành kịch bản xuất sắc nhờ việc lập hành trình phân tách nhịp nhàng. Hai xe đi qua điểm giao cắt lệch thời gian nên không hề xảy ra va chạm.

---

## Level 4 - Scenario 030 (Multi-AGV Deadlock Resolution)
**Yêu cầu**: 3 xe AGV (`AGV_01`, `AGV_02`, `AGV_03`) hoạt động đồng thời tại các khu vực đường hẹp đan xen, với 3 yêu cầu vận tải độc lập diễn ra cùng lúc.

| Metric / Model | Gemini 2.5 Flash | Qwen Max (Cloud) | Llama 3.3 70B (Groq) |
| :--- | :---: | :---: | :---: |
| **Trạng thái chạy** | **SUCCESS** | **FAILED** | **FAILED** |
| **Độ trễ API (ms)** | ~31766.8 | ~13309.0 | ~3400.0 |
| **Thời gian mô phỏng (s)**| 85.40 | 9.70 | 6.20 |
| **Số vụ va chạm** | 0 | 1 | 1 |
| **Pin AGV_01 (%)** | 93.35% | 98.08% | 98.80% |
| **Pin AGV_02 (%)** | 85.04% | 98.08% | 98.80% |
| **Pin AGV_03 (%)** | 83.37% | 100.00% | 98.80% |

### Ghi chú lỗi (Notes on Failed Models):
* **Qwen Max (Cloud)**: Thất bại do lỗi lập lộ trình trống cho xe `AGV_03` ("Warning - Accepted order has no nodes"), dẫn đến xe này đứng im tại chỗ cản đường và bị 2 xe còn lại đâm vào ở giây thứ 9.70.
* **Llama 3.3 70B (Groq)**: Thất bại do lỗi va chạm giao lộ hẹp ở giây thứ 6.20 vì không phân luồng xe đi vòng.

---

# Các mục tiêu tiếp theo
- Thử nghiệm thêm các models có lượng tham số lớn hơn
- Thử nghiệm thêm các layout có độ khó cao hơn
- Thử nghiệm thêm các scenario có độ khó cao hơn
- Sử dụng các biện pháp để dùng chung cho các APIs, tránh phải viết adapter cho từng cái
- Tìm kiếm và thử nghiệm được các cases xuất hiện trong thực tế
- Bổ sung câu lệnh can thiệp từ người dùng khi xe đang chạy