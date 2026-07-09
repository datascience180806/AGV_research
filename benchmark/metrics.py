from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ScenarioMetrics:
    """Các chỉ số đo lường hiệu năng của 1 Scenario"""
    scenario_id: str
    success: bool = False
    failure_reason: Optional[str] = None  # "collision", "timeout", "battery_dead", "invalid_order", "invalid_json", "restricted_zone_violation", "incorrect_diagnosis"
    model_latency_ms: float = 0.0
    simulation_time_seconds: float = 0.0
    collision_count: int = 0
    initial_battery: Dict[str, float] = field(default_factory=dict)
    final_battery: Dict[str, float] = field(default_factory=dict)
    total_requests: int = 0
    completed_requests: int = 0
    raw_response: str = ""
    
    # Chỉ số chẩn đoán lỗi mới (Anomaly Detection & Diagnosis Metrics)
    detection_accuracy: float = 0.0
    false_positive_count: int = 0
    detection_latency_seconds: Optional[float] = None
    correct_root_cause: bool = False
    diagnoses_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "model_latency_ms": self.model_latency_ms,
            "simulation_time_seconds": self.simulation_time_seconds,
            "collision_count": self.collision_count,
            "initial_battery": self.initial_battery,
            "final_battery": self.final_battery,
            "total_requests": self.total_requests,
            "completed_requests": self.completed_requests,
            "detection_accuracy": self.detection_accuracy,
            "false_positive_count": self.false_positive_count,
            "detection_latency_seconds": self.detection_latency_seconds,
            "correct_root_cause": self.correct_root_cause,
            "diagnoses_log": self.diagnoses_log
        }

