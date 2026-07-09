from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ModelResponse:
    """Đầu ra chuẩn hóa từ AI Model cho điều khiển"""
    status: str  # "SUCCESS" hoặc "FAILED"
    orders: Dict[str, Any]  # Key: serial_number, Value: VDA5050 Order dict
    raw_response: str  # Phản hồi thô của model
    latency_ms: float  # Thời gian gọi API (ms)
    error_message: Optional[str] = None

@dataclass
class ModelDiagnosisResponse:
    """Đầu ra chuẩn hóa từ AI Model cho chẩn đoán lỗi"""
    status: str  # "SUCCESS" hoặc "FAILED"
    diagnosis: Dict[str, Any]  # Kết quả JSON chẩn đoán từ model
    raw_response: str  # Phản hồi thô
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
        raise NotImplementedError("Hãy override phương thức generate_orders() trong class adapter con.")

    def diagnose_stream(
        self,
        factory_layout: Dict[str, Any],
        packet_window: List[Dict[str, Any]],
        agv_profiles: List[Dict[str, Any]]
    ) -> ModelDiagnosisResponse:
        """
        Gửi luồng gói tin của xe AGV cho Model để chẩn đoán sự cố sớm.
        """
        raise NotImplementedError("Hãy override phương thức diagnose_stream() trong class adapter con.")

