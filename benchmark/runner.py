import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

import config
from main import VehicleSimulator
from protocol.vda_2_0_0.vda5050_2_0_0_order import Order
from protocol.vda_2_0_0.vda5050_2_0_0_state import ActionStatus
from models.base_adapter import BaseModelAdapter
from benchmark.metrics import ScenarioMetrics
from benchmark.packet_logger import PacketLogger

# New diagnostic components
from benchmark.sliding_window import SlidingWindowBuffer
from benchmark.diagnosis_evaluator import DiagnosisEvaluator
from operations.fault_injector import FaultInjector

# Virtual sensors
from sensors.weight_sensor import WeightSensor
from sensors.lidar_scanner import LidarScanner
from sensors.temperature_monitor import TemperatureMonitor
from sensors.encoder_sensor import EncoderSensor
from sensors.battery_monitor import BatteryMonitor

class BenchmarkRunner:
    """Điều phối và chạy thử nghiệm Benchmark cho 1 Scenario (Chẩn đoán lỗi)"""

    def __init__(self, model_adapter: BaseModelAdapter, output_base_dir: str = "results"):
        self.model_adapter = model_adapter
        self.output_base_dir = output_base_dir

    def run_scenario(self, scenario_path: str) -> ScenarioMetrics:
        # 1. Load kịch bản và sơ đồ nhà máy
        with open(scenario_path, "r", encoding="utf-8") as f:
            scenario = json.load(f)

        layout_name = scenario.get("factory_layout")
        layout_path = f"factory_layouts/{layout_name}.json"
        with open(layout_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        scenario_id = scenario["scenario_id"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = getattr(self.model_adapter, "model_name", "unknown_model")
        safe_model_name = model_name.replace("/", "_").replace(":", "_")
        
        # Thư mục lưu kết quả của lần test này
        run_dir = os.path.join(self.output_base_dir, f"{safe_model_name}_{timestamp}_{scenario_id}")
        logger = PacketLogger(run_dir)
        
        logger.log_event("scenario_loaded", "INPUT", scenario)
        logger.log_event("layout_loaded", "INPUT", layout)

        # 2. Khởi tạo Route Controller (Hardcoded router cho kịch bản)
        orders = {}
        route_script = scenario.get("route_script")
        if route_script == "multi_zone_factory_ops":
            from operations.multi_zone_factory_ops import MultiZoneFactoryRouter
            router = MultiZoneFactoryRouter(layout, scenario)
            orders = router.get_orders()
            print(f"Loaded hardcoded router: {route_script}")
        else:
            print(f"Warning: No hardcoded router found for script '{route_script}'. Falling back.")

        # 3. Khởi tạo Simulator cho từng AGV
        simulators: Dict[str, VehicleSimulator] = {}
        base_config = config.get_config()
        metrics = ScenarioMetrics(
            scenario_id=scenario_id,
            total_requests=len(scenario.get("transport_requests", [])),
        )

        agv_profiles = []
        for agv_info in scenario.get("agvs", []):
            serial = agv_info["serial_number"]
            agv_cfg = config.Config(
                mqtt_broker=base_config.mqtt_broker,
                vehicle=config.VehicleConfig(
                    manufacturer=base_config.vehicle.manufacturer,
                    serial_number=serial,
                    vda_version=base_config.vehicle.vda_version,
                    vda_full_version=base_config.vehicle.vda_full_version
                ),
                settings=config.Settings(
                    action_time=2.0,
                    speed=agv_info["speed"],
                    robot_count=1,
                    state_frequency=1,
                    visualization_frequency=1,
                    map_id=layout["map_id"]
                )
            )
            sim = VehicleSimulator(agv_cfg)
            sim.state.agv_position.x = agv_info["initial_position"]["x"]
            sim.state.agv_position.y = agv_info["initial_position"]["y"]
            sim.state.battery_state.battery_charge = agv_info["battery_charge"]
            simulators[serial] = sim
            metrics.initial_battery[serial] = agv_info["battery_charge"]
            
            # Lưu profile để gửi cho AI
            agv_profiles.append({
                "serial_number": serial,
                "max_load_kg": agv_info.get("max_load_kg", 150.0),
                "speed": agv_info["speed"],
                "capabilities": agv_info.get("capabilities", [])
            })

        # Bơm Orders tự động vào các AGV
        for serial, order_data in orders.items():
            if serial in simulators:
                sim = simulators[serial]
                order_data["headerId"] = 0
                order_data["timestamp"] = sim.state.timestamp
                order_data["version"] = sim.config.vehicle.vda_full_version
                order_data["manufacturer"] = sim.config.vehicle.manufacturer
                order_data["serialNumber"] = serial
                parsed_order = Order.from_dict(order_data)
                sim.order_accept_procedure(parsed_order)
                logger.log_event("order_injected", "INTERNAL", {"agv": serial, "order_id": parsed_order.order_id})

        # 4. Khởi tạo Fault Injector, Sliding Window & Virtual Sensors
        fault_injector = FaultInjector(scenario.get("fault_injection", []))
        sliding_window = SlidingWindowBuffer(window_size=20)
        
        sensors = {
            serial: {
                "weight": WeightSensor(max_capacity_kg=agv_info.get("max_load_kg", 150.0)),
                "lidar": LidarScanner(range_m=5.0),
                "temperature": TemperatureMonitor(baseline_c=25.0),
                "encoder": EncoderSensor(),
                "battery": BatteryMonitor(charge_percent=agv_info["battery_charge"])
            }
            for serial, agv_info in {a["serial_number"]: a for a in scenario.get("agvs", [])}.items()
        }

        # 5. Vòng lặp giả lập và chẩn đoán lỗi
        tick_time = 0.05
        max_time = scenario.get("constraints", {}).get("max_simulation_time_s", 120)
        max_ticks = int(max_time / tick_time)
        diagnosis_interval_s = scenario.get("constraints", {}).get("diagnosis_interval_s", 5.0)
        
        diagnoses_log = []
        sim_success = False
        failure_reason = None
        
        print("Starting in-memory simulation run with online diagnostics...")
        for tick in range(1, max_ticks + 1):
            elapsed_time = tick * tick_time
            metrics.simulation_time_seconds = elapsed_time

            # Cập nhật Fault Injector
            fault_injector.update(elapsed_time)

            # Chạy iterate cho từng AGV
            for serial, sim in simulators.items():
                # Tác động lỗi vào dung lượng pin nếu có lỗi battery_leak
                if fault_injector.is_fault_active(serial, "battery_leak"):
                    mult = fault_injector.get_fault_multiplier(serial, "battery_leak")
                    base_drain = 0.015 if sim.state.driving else 0.002
                    sim.state.battery_state.battery_charge = max(0.0, round(sim.state.battery_state.battery_charge - base_drain * mult, 3))

                sim.state_iterate()
                
                # Tạo và gửi gói tin cảm biến
                load_weight = 0.0
                # Tìm tải trọng từ transport requests đang gán cho xe
                for req in scenario.get("transport_requests", []):
                    if req["assigned_agv"] == serial:
                        # Nếu đã qua pickup node mà chưa qua dropoff, xe đang chở hàng
                        # Trong sim đơn giản này, xem như chở tải trọng định cấu hình
                        load_weight = req.get("payload_weight_kg", 50.0)
                
                # Chạy ảo cảm biến
                weight_data = sensors[serial]["weight"].get_data(load_weight)
                lidar_data = sensors[serial]["lidar"].get_data(5.0) # obstacle dist
                temp_data = sensors[serial]["temperature"].get_data(sim.state.driving)
                encoder_data = sensors[serial]["encoder"].get_data(sim.state.driving, sim.config.settings.speed, tick_time)
                battery_data = sensors[serial]["battery"].get_data(sim.state.battery_state.battery_charge, fault_injector.is_fault_active(serial, "battery_leak"))

                sensor_packet = {
                    "timestamp": datetime.now().isoformat(),
                    "agv_id": serial,
                    "packet_type": "sensor_data",
                    "sensors": {
                        "weight": weight_data,
                        "lidar": lidar_data,
                        "temperature": temp_data,
                        "encoder": encoder_data,
                        "battery": battery_data
                    }
                }

                # Push to sliding window
                state_pkt = sim.state.to_dict()
                state_pkt["agv_id"] = serial
                state_pkt["packet_type"] = "state"
                sliding_window.push(state_pkt)
                sliding_window.push(sensor_packet)

            # Log trạng thái tick
            states_log = {s: sim.state.to_dict() for s, sim in simulators.items()}
            logger.log_event("sim_tick_state", "INTERNAL", states_log, elapsed_time=elapsed_time)

            # Thực hiện chẩn đoán định kỳ (mỗi diagnosis_interval_s giây)
            if tick % int(diagnosis_interval_s / tick_time) == 0:
                print(f"Calling model for diagnostics at {elapsed_time}s...")
                current_window = sliding_window.get_window()
                
                diag_start = time.time()
                diag_resp = self.model_adapter.diagnose_stream(
                    factory_layout=layout,
                    packet_window=current_window,
                    agv_profiles=agv_profiles
                )
                diag_latency = (time.time() - diag_start) * 1000
                metrics.model_latency_ms += diag_latency
                
                if diag_resp.status == "SUCCESS":
                    diagnoses_log.append({
                        "elapsed_time": elapsed_time,
                        "diagnosis": diag_resp.diagnosis
                    })
                    logger.log_event("ai_diagnosis", "OUTPUT", {
                        "elapsed_time": elapsed_time,
                        "diagnosis": diag_resp.diagnosis
                    }, elapsed_time=elapsed_time)
                else:
                    print(f"Model diagnosis failed at {elapsed_time}s: {diag_resp.error_message}")

            # Kiểm tra hoàn thành tất cả nhiệm vụ di chuyển
            all_done = True
            for serial, sim in simulators.items():
                if sim.state.node_states:
                    last_node_seq = max(node.sequence_id for node in sim.state.node_states)
                    reached_last_node = sim.state.last_node_sequence_id >= last_node_seq
                else:
                    reached_last_node = True
                    
                has_pending_actions = any(a.action_status != ActionStatus.FINISHED for a in sim.state.action_states)
                if not reached_last_node or has_pending_actions:
                    all_done = False
                    break
            
            if all_done:
                sim_success = True
                break

            time.sleep(tick_time)

        # 6. Đánh giá chất lượng chẩn đoán
        for serial, sim in simulators.items():
            metrics.final_battery[serial] = sim.state.battery_state.battery_charge

        eval_results = DiagnosisEvaluator.evaluate(diagnoses_log, scenario.get("ground_truth", {}))
        
        metrics.success = sim_success and (eval_results["detection_accuracy"] >= 80.0)
        if not sim_success:
            metrics.failure_reason = "timeout"
        elif eval_results["detection_accuracy"] < 80.0:
            metrics.failure_reason = "incorrect_diagnosis"

        metrics.detection_accuracy = eval_results["detection_accuracy"]
        metrics.false_positive_count = eval_results["false_positive_count"]
        metrics.detection_latency_seconds = eval_results["detection_latency_seconds"]
        metrics.correct_root_cause = eval_results["correct_root_cause"]
        metrics.diagnoses_log = diagnoses_log

        print(f"Diagnosis accuracy: {metrics.detection_accuracy}%")
        print(f"Detection latency: {metrics.detection_latency_seconds}s")
        print(f"Correct root cause analysis: {metrics.correct_root_cause}")

        # Ghi nhận log cuối cùng
        logger.log_event("simulation_finished", "OUTPUT", metrics.to_dict(), elapsed_time=metrics.simulation_time_seconds)
        self._save_summary(run_dir, metrics)
        logger.close()
        return metrics

    def _save_summary(self, run_dir: str, metrics: ScenarioMetrics):
        """Lưu file tóm tắt kết quả kiểm tra"""
        os.makedirs(run_dir, exist_ok=True)
        summary_path = os.path.join(run_dir, "benchmark_report.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(metrics.to_dict(), f, indent=4, ensure_ascii=False)
