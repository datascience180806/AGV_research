import math
from typing import Dict, List, Any, Tuple
from benchmark.metrics import ScenarioMetrics

class ScenarioEvaluator:
    """Đánh giá kịch bản chạy thử nghiệm"""

    @staticmethod
    def check_collision_agv_vs_agv(agv_positions: Dict[str, Tuple[float, float]], tolerance: float = 0.6) -> List[Tuple[str, str]]:
        """Kiểm tra va chạm giữa các AGV"""
        collisions = []
        serials = list(agv_positions.keys())
        for i in range(len(serials)):
            for j in range(i + 1, len(serials)):
                s1, s2 = serials[i], serials[j]
                p1, p2 = agv_positions[s1], agv_positions[s2]
                dist = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                if dist < tolerance:
                    collisions.append((s1, s2))
        return collisions

    @staticmethod
    def check_collision_with_obstacles(
        agv_positions: Dict[str, Tuple[float, float]], 
        obstacles: List[Dict[str, Any]], 
        tolerance: float = 0.4
    ) -> List[Tuple[str, str]]:
        """Kiểm tra va chạm giữa AGV và vật cản"""
        collisions = []
        for serial, (ax, ay) in agv_positions.items():
            for obs in obstacles:
                obs_type = obs.get("type")
                obs_id = obs.get("obstacle_id")
                
                if obs_type == "pillar":
                    center = obs.get("center", [0.0, 0.0])
                    radius = obs.get("radius", 0.5)
                    dist = math.sqrt((ax - center[0])**2 + (ay - center[1])**2)
                    if dist < (radius + tolerance):
                        collisions.append((serial, obs_id))
                        
                elif obs_type == "wall":
                    # Đơn giản hóa: Kiểm tra nếu điểm (ax, ay) nằm gần các đoạn thẳng của tường
                    vertices = obs.get("vertices", [])
                    for k in range(len(vertices) - 1):
                        p1 = vertices[k]
                        p2 = vertices[k+1]
                        # Tính khoảng cách từ điểm (ax, ay) đến đoạn thẳng p1-p2
                        dist = ScenarioEvaluator._dist_to_segment(ax, ay, p1[0], p1[1], p2[0], p2[1])
                        if dist < tolerance:
                            collisions.append((serial, obs_id))
                            break
        return collisions

    @staticmethod
    def _dist_to_segment(px, py, x1, y1, x2, y2) -> float:
        """Tính khoảng cách từ điểm p đến đoạn thẳng (x1,y1)-(x2,y2)"""
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1)**2 + (py - y1)**2)
            
        t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
        t = max(0, min(1, t))
        
        nearest_x = x1 + t * dx
        nearest_y = y1 + t * dy
        return math.sqrt((px - nearest_x)**2 + (py - nearest_y)**2)

    @staticmethod
    def check_restricted_zone_violation(
        agv_positions: Dict[str, Tuple[float, float]],
        zones: List[Dict[str, Any]]
    ) -> List[Tuple[str, str]]:
        """Kiểm tra xe AGV xâm nhập vào vùng hạn chế di chuyển (restricted zone)"""
        violations = []
        for serial, (ax, ay) in agv_positions.items():
            for zone in zones:
                if zone.get("type") == "restricted":
                    bounds = zone.get("bounds", {})
                    x_min = bounds.get("x_min", 0.0)
                    x_max = bounds.get("x_max", 0.0)
                    y_min = bounds.get("y_min", 0.0)
                    y_max = bounds.get("y_max", 0.0)
                    
                    if x_min <= ax <= x_max and y_min <= ay <= y_max:
                        violations.append((serial, zone.get("zone_id", "RESTRICTED_ZONE")))
        return violations
