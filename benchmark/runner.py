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
from benchmark.evaluator import ScenarioEvaluator
from benchmark.packet_logger import PacketLogger

class BenchmarkRunner:
    """Điều phối và chạy thử nghiệm Benchmark cho 1 Scenario"""

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
        # Thay thế ký tự đặc biệt (/, :) để hợp lệ trên hệ thống tập tin Windows
        safe_model_name = model_name.replace("/", "_").replace(":", "_")
        
        # Thư mục lưu kết quả của lần test này
        run_dir = os.path.join(self.output_base_dir, f"{safe_model_name}_{timestamp}_{scenario_id}")
        logger = PacketLogger(run_dir)
        
        logger.log_event("scenario_loaded", "INPUT", scenario)
        logger.log_event("layout_loaded", "INPUT", layout)

        # 2. Xây dựng thông tin đầu vào gửi cho AI Model
        agv_states = []
        for agv_info in scenario.get("agvs", []):
            agv_states.append({
                "serial_number": agv_info["serial_number"],
                "position": agv_info["initial_position"],
                "battery_charge": agv_info["battery_charge"],
                "speed": agv_info["speed"],
                "capabilities": agv_info.get("capabilities", [])
            })

        logger.log_event("model_request_sent", "INPUT", {
            "agv_states": agv_states,
            "transport_requests": scenario["transport_requests"]
        })

        # 3. Gọi model để sinh chỉ thị di chuyển (VDA5050 Orders)
        print(f"Calling model '{model_name}' for scenario '{scenario_id}'...")
        response = self.model_adapter.generate_orders(
            factory_layout=layout,
            agv_states=agv_states,
            transport_requests=scenario["transport_requests"],
            constraints=scenario.get("constraints", {})
        )

        logger.log_event("model_response_received", "OUTPUT", {
            "status": response.status,
            "latency_ms": response.latency_ms,
            "orders": response.orders,
            "error_message": response.error_message
        })

        # Khởi tạo metrics
        metrics = ScenarioMetrics(
            scenario_id=scenario_id,
            model_latency_ms=response.latency_ms,
            total_requests=len(scenario["transport_requests"]),
            raw_response=response.raw_response
        )

        if response.status != "SUCCESS":
            metrics.success = False
            metrics.failure_reason = "invalid_json" if "JSON" in str(response.error_message) else "api_error"
            self._save_summary(run_dir, metrics)
            logger.close()
            return metrics

        # 4. Khởi tạo Simulator cho từng AGV
        simulators: Dict[str, VehicleSimulator] = {}
        base_config = config.get_config()

        for agv_info in scenario.get("agvs", []):
            serial = agv_info["serial_number"]
            # Tạo config riêng cho từng AGV
            agv_cfg = config.Config(
                mqtt_broker=base_config.mqtt_broker,
                vehicle=config.VehicleConfig(
                    manufacturer=base_config.vehicle.manufacturer,
                    serial_number=serial,
                    vda_version=base_config.vehicle.vda_version,
                    vda_full_version=base_config.vehicle.vda_full_version
                ),
                settings=config.Settings(
                    action_time=scenario.get("constraints", {}).get("action_time", 2.0),
                    speed=agv_info["speed"],
                    robot_count=1,
                    state_frequency=1,
                    visualization_frequency=1,
                    map_id=layout["map_id"]
                )
            )
            sim = VehicleSimulator(agv_cfg)
            # Thiết lập vị trí và pin ban đầu theo kịch bản
            sim.state.agv_position.x = agv_info["initial_position"]["x"]
            sim.state.agv_position.y = agv_info["initial_position"]["y"]
            sim.state.battery_state.battery_charge = agv_info["battery_charge"]
            simulators[serial] = sim
            metrics.initial_battery[serial] = agv_info["battery_charge"]

        # 5. Bơm Orders nhận được từ model vào simulator
        orders_received = response.orders
        for serial, order_data in orders_received.items():
            if serial in simulators:
                try:
                    # Điền thông tin header/metadata còn thiếu vào order_data trước khi parse
                    sim = simulators[serial]
                    order_data["headerId"] = order_data.get("headerId", 0)
                    order_data["timestamp"] = order_data.get("timestamp", sim.state.timestamp)
                    order_data["version"] = order_data.get("version", sim.config.vehicle.vda_full_version)
                    order_data["manufacturer"] = order_data.get("manufacturer", sim.config.vehicle.manufacturer)
                    order_data["serialNumber"] = order_data.get("serialNumber", serial)
                    
                    # Chuyển đổi dữ liệu JSON thành object VDA5050 Order
                    parsed_order = Order.from_dict(order_data)
                    simulators[serial].order_accept_procedure(parsed_order)
                    logger.log_event("order_injected", "INTERNAL", {"agv": serial, "order_id": parsed_order.order_id})
                except Exception as e:
                    print(f"Error parsing order for {serial}: {e}")
                    metrics.success = False
                    metrics.failure_reason = "invalid_order"
                    self._save_summary(run_dir, metrics)
                    logger.close()
                    return metrics

        # Trạng thái theo dõi sự kiện cho trực quan hóa
        last_nodes = {serial: sim.state.last_node_sequence_id for serial, sim in simulators.items()}
        action_statuses = {
            serial: {a.action_id: a.action_status for a in sim.state.action_states}
            for serial, sim in simulators.items()
        }

        # 6. Vòng lặp giả lập (Simulation Tick Loop)
        # Mỗi tick đại diện cho 50ms (0.05 giây)
        tick_time = 0.05
        max_time = scenario.get("constraints", {}).get("max_time_seconds", 120)
        max_ticks = int(max_time / tick_time)
        
        sim_success = False
        failure_reason = None
        
        print("Starting in-memory simulation run...")
        for tick in range(1, max_ticks + 1):
            elapsed_time = tick * tick_time
            metrics.simulation_time_seconds = elapsed_time

            # Chạy iterate cho từng AGV
            for serial, sim in simulators.items():
                sim.state_iterate()
                
                # Kiểm tra xem xe có đến trạm mới không
                if sim.state.last_node_sequence_id != last_nodes[serial]:
                    last_nodes[serial] = sim.state.last_node_sequence_id
                    logger.log_event("agv_arrived_node", "EVENT", {
                        "agv": serial, 
                        "node_id": sim.state.last_node_id, 
                        "sequence_id": sim.state.last_node_sequence_id
                    }, elapsed_time=elapsed_time)
                
                # Kiểm tra trạng thái Action thay đổi
                for a in sim.state.action_states:
                    old_status = action_statuses[serial].get(a.action_id, ActionStatus.WAITING)
                    if a.action_status != old_status:
                        action_statuses[serial][a.action_id] = a.action_status
                        logger.log_event("agv_action_update", "EVENT", {
                            "agv": serial,
                            "action_id": a.action_id,
                            "action_type": a.action_type,
                            "status": a.action_status.value
                        }, elapsed_time=elapsed_time)
                
            # Thu thập vị trí để kiểm tra va chạm
            agv_positions = {s: (sim.state.agv_position.x, sim.state.agv_position.y) for s, sim in simulators.items()}
            
            # Ghi log trạng thái mỗi tick giả lập để vẽ hình mượt mà
            states_log = {s: sim.state.to_dict() for s, sim in simulators.items()}
            logger.log_event("sim_tick_state", "INTERNAL", states_log, elapsed_time=elapsed_time)

            # A. Kiểm tra hết pin
            battery_dead = False
            for serial, sim in simulators.items():
                if sim.state.battery_state.battery_charge <= 0:
                    battery_dead = True
                    failure_reason = "battery_dead"
                    break
            if battery_dead:
                break

            # B. Kiểm tra va chạm giữa các xe
            agv_collisions = ScenarioEvaluator.check_collision_agv_vs_agv(agv_positions)
            if agv_collisions:
                metrics.collision_count += len(agv_collisions)
                failure_reason = "collision"
                logger.log_event("collision_detected", "EVENT", {"collisions": agv_collisions}, elapsed_time=elapsed_time)
                break

            # C. Kiểm tra va chạm vật cản
            obstacle_collisions = ScenarioEvaluator.check_collision_with_obstacles(agv_positions, layout.get("obstacles", []))
            if obstacle_collisions:
                metrics.collision_count += len(obstacle_collisions)
                failure_reason = "collision"
                logger.log_event("collision_with_obstacle_detected", "EVENT", {"collisions": obstacle_collisions}, elapsed_time=elapsed_time)
                break

            # D. Kiểm tra hoàn thành tất cả nhiệm vụ
            # Một kịch bản coi như hoàn thành khi tất cả các simulator hoàn thành đơn hàng 
            # (không còn node_states hoặc chỉ còn node cuối cùng và không có action nào chưa hoàn thành)
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

            # Sleep to let real-world time progress for action timers
            time.sleep(tick_time)

        # Xác định kết quả cuối cùng
        for serial, sim in simulators.items():
            metrics.final_battery[serial] = sim.state.battery_state.battery_charge

        if sim_success:
            metrics.success = True
            metrics.completed_requests = metrics.total_requests
            print(f"Scenario completed successfully in {metrics.simulation_time_seconds:.2f} seconds!")
        else:
            metrics.success = False
            metrics.failure_reason = failure_reason if failure_reason else "timeout"
            print(f"Scenario failed! Reason: {metrics.failure_reason}")

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
