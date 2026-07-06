from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ModelResponse:
    """Đầu ra chuẩn hóa từ AI Model"""
    status: str  # "SUCCESS" hoặc "FAILED"
    orders: Dict[str, Any]  # Key: serial_number, Value: VDA5050 Order dict
    raw_response: str  # Phản hồi thô của model
    latency_ms: float  # Thời gian gọi API (ms)
    error_message: Optional[str] = None

class BaseModelAdapter:
    """Lớp cơ sở trừu tượng cho tất cả AI Model Adapters"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def generate_orders(
        self,
        factory_layout: Dict[str, Any],
        agv_states: List[Dict[str, Any]],
        transport_requests: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> ModelResponse:
        """
        Gửi ngữ cảnh kịch bản cho Model và yêu cầu trả về danh sách VDA5050 Orders cho các xe.

        Args:
            factory_layout: Bản đồ nhà máy (nodes, edges, obstacles, zones)
            agv_states: Trạng thái hiện tại của tất cả AGVs
            transport_requests: Các đơn hàng vận chuyển cần xử lý
            constraints: Ràng buộc kịch bản (max_time, collision_tolerance...)

        Returns:
            ModelResponse: Đối tượng chứa chỉ thị di chuyển dạng VDA5050 và thông số hiệu năng
        """
        raise NotImplementedError("Hãy override phương thức generate_orders() trong class adapter con.")
