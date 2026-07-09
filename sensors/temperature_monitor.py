import random

class TemperatureMonitor:
    """Simulates motor and electronics temperature monitoring"""
    def __init__(self, baseline_c: float = 25.0):
        self.baseline_c = baseline_c
        self.left_motor_temp = baseline_c
        self.right_motor_temp = baseline_c

    def get_data(self, is_driving: bool) -> dict:
        if is_driving:
            self.left_motor_temp += random.uniform(0.1, 0.4)
            self.right_motor_temp += random.uniform(0.1, 0.4)
        else:
            self.left_motor_temp = max(self.baseline_c, self.left_motor_temp - random.uniform(0.1, 0.3))
            self.right_motor_temp = max(self.baseline_c, self.right_motor_temp - random.uniform(0.1, 0.3))
            
        return {
            "motor_left_c": round(self.left_motor_temp, 1),
            "motor_right_c": round(self.right_motor_temp, 1),
            "battery_c": round(self.baseline_c + (self.left_motor_temp - self.baseline_c) * 0.4 + random.uniform(0, 1.0), 1),
            "ambient_c": round(self.baseline_c, 1),
            "motor_warning_threshold_c": 80.0
        }
