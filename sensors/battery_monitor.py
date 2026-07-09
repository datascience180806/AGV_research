import random

class BatteryMonitor:
    """Simulates detailed battery metrics, cell health, and drain rates"""
    def __init__(self, charge_percent: float = 100.0):
        self.charge_percent = charge_percent
        self.cells = [98, 98, 97, 98, 96, 98]

    def get_data(self, current_charge: float, leak_active: bool) -> dict:
        self.charge_percent = current_charge
        
        # Simulate cells: if battery leak is active, cell #4 drops significantly
        if leak_active:
            self.cells[3] = max(10, self.cells[3] - 2)
            cell_health = list(self.cells)
            drain_rate = 14.4  # High discharge rate per minute
        else:
            cell_health = list(self.cells)
            drain_rate = 1.8   # Normal discharge rate per minute
            
        voltage = 48.0 * (self.charge_percent / 100.0)
        current = 15.0 if leak_active else 3.5
        
        return {
            "voltage_v": round(voltage, 2),
            "current_a": round(current, 2),
            "charge_percent": round(self.charge_percent, 1),
            "drain_rate_pct_per_min": drain_rate,
            "estimated_remaining_min": round((self.charge_percent / drain_rate) if drain_rate > 0 else 999.0, 1),
            "cell_health": cell_health,
            "temperature_c": round(35.0 + (drain_rate * 1.5), 1)
        }
