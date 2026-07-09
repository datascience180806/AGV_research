class FaultInjector:
    """Injects VDA 5050 and sensor faults into AGVs at runtime based on scenario definition"""
    def __init__(self, fault_config: list):
        self.fault_config = fault_config or []
        self.active_faults = {} # key: (agv, fault_type), value: fault parameters

    def update(self, current_time_s: float):
        """Evaluate triggers and activate faults"""
        for f in self.fault_config:
            fault_id = f.get("fault_id")
            if fault_id in self.active_faults:
                continue

            trigger = f.get("trigger", {})
            trigger_type = trigger.get("type")
            
            should_trigger = False
            if trigger_type == "time":
                if current_time_s >= trigger.get("at_second", 0.0):
                    should_trigger = True

            if should_trigger:
                agv = f.get("target_agv")
                fault_type = f.get("type")
                params = f.get("parameters", {})
                self.active_faults[(agv, fault_type)] = params
                print(f"FAULT INJECTOR: Activated '{fault_type}' on '{agv}' at {current_time_s}s: {params.get('description')}")

    def is_fault_active(self, agv_id: str, fault_type: str) -> bool:
        """Returns True if the specified fault is active on the AGV"""
        return (agv_id, fault_type) in self.active_faults

    def get_fault_multiplier(self, agv_id: str, fault_type: str) -> float:
        """Returns the multiplier or parameter associated with an active fault, defaults to 1.0"""
        fault_key = (agv_id, fault_type)
        if fault_key in self.active_faults:
            return self.active_faults[fault_key].get("drain_rate_multiplier", 1.0)
        return 1.0
