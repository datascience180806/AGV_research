import random

class LidarScanner:
    """Simulates distance scanning and blocked sectors (e.g. dust/blind spots)"""
    def __init__(self, range_m: float = 5.0):
        self.range_m = range_m
        self.degraded = False

    def get_data(self, nearest_obstacle_dist: float) -> dict:
        dist = nearest_obstacle_dist
        if self.degraded:
            # Simulate dirty lens returning false obstacles close to the scanner
            dist = random.uniform(0.1, 0.4)
            blocked_sectors = [45, 90]
            scan_quality = "degraded"
        else:
            blocked_sectors = []
            scan_quality = "good"
            
        return {
            "scan_points": 360,
            "nearest_obstacle_m": round(dist, 2),
            "obstacle_direction_deg": random.choice([0, 45, 90, 180]),
            "scan_quality": scan_quality,
            "blocked_sectors": blocked_sectors
        }
