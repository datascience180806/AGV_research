import random

class WeightSensor:
    """Simulates payload weight and overloading alerts"""
    def __init__(self, max_capacity_kg: float = 150.0):
        self.max_capacity_kg = max_capacity_kg

    def get_data(self, current_load_kg: float) -> dict:
        # Add slight noise
        measured = max(0.0, current_load_kg + random.normalvariate(0, 0.2))
        overload = measured > self.max_capacity_kg
        return {
            "current_load_kg": round(measured, 2),
            "max_capacity_kg": self.max_capacity_kg,
            "load_percentage": round((measured / self.max_capacity_kg) * 100.0, 1),
            "overload_warning": overload
        }
