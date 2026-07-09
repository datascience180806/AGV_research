import random

class EncoderSensor:
    """Simulates wheel encoder wheel speeds and odometer"""
    def __init__(self):
        self.odometer_m = 0.0

    def get_data(self, is_driving: bool, speed_mps: float, elapsed_time_s: float) -> dict:
        if is_driving:
            delta_dist = speed_mps * elapsed_time_s
            self.odometer_m += delta_dist
            left_rpm = (speed_mps * 60.0) / (0.2 * 3.14159) # D=0.2m wheel
            right_rpm = left_rpm + random.normalvariate(0, 0.5)
        else:
            left_rpm = 0.0
            right_rpm = 0.0
            
        return {
            "left_wheel_rpm": round(left_rpm, 1),
            "right_wheel_rpm": round(right_rpm, 1),
            "speed_mps": round(speed_mps if is_driving else 0.0, 2),
            "odometer_m": round(self.odometer_m, 2),
            "wheel_slip_detected": False
        }
