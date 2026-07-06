import json
import os
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation

def load_benchmark_run(run_dir):
    """Đọc dữ liệu layout và lịch sử di chuyển từ kết quả benchmark"""
    log_path = os.path.join(run_dir, "packet_log.jsonl")
    if not os.path.exists(log_path):
        print(f"Error: Không tìm thấy file {log_path}")
        return None, []

    layout = None
    tick_states = []

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            
            # Lấy layout nhà máy từ log
            if entry.get("type") == "layout_loaded":
                layout = entry.get("data")
            
            # Thu thập lịch sử trạng thái vị trí của các xe qua từng tick
            elif entry.get("type") == "sim_tick_state":
                tick_states.append({
                    "elapsed_time": entry.get("elapsed_time", 0.0),
                    "agvs": entry.get("data", {})
                })
                
    return layout, tick_states

def play_animation(layout, tick_states):
    if not layout or not tick_states:
        print("Error: Không có dữ liệu để hiển thị.")
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 1. Vẽ sơ đồ nhà máy làm nền (Background)
    dims = layout.get("dimensions", {"width": 15.0, "height": 15.0})
    ax.set_xlim(-1, dims["width"] + 1)
    ax.set_ylim(-1, dims["height"] + 1)
    ax.set_aspect('equal')
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title(f"Benchmark Playback - Map: {layout.get('layout_name')}", fontsize=14, fontweight="bold")
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")

    # Vẽ Zones
    for zone in layout.get("zones", []):
        bounds = zone.get("bounds", {})
        x_min, y_min = bounds.get("x_min", 0.0), bounds.get("y_min", 0.0)
        x_max, y_max = bounds.get("x_max", 0.0), bounds.get("y_max", 0.0)
        width, height = x_max - x_min, y_max - y_min
        color = "yellow" if zone.get("type") == "charging" else "orange" if zone.get("type") == "restricted" else "purple" if zone.get("type") == "assembly" else "green"
        rect = patches.Rectangle((x_min, y_min), width, height, linewidth=1, 
                                 edgecolor=color, facecolor=color, alpha=0.1, label=f"Zone: {zone['zone_id']}")
        ax.add_patch(rect)

    # Vẽ Obstacles
    for obs in layout.get("obstacles", []):
        obs_type = obs.get("type", "")
        if obs_type == "wall":
            vertices = obs.get("vertices", [])
            if len(vertices) >= 2:
                if vertices[0] == vertices[-1] or len(vertices) > 2:
                    poly = patches.Polygon(vertices, closed=True, edgecolor="darkred", facecolor="red", alpha=0.2)
                    ax.add_patch(poly)
                else:
                    ax.plot([v[0] for v in vertices], [v[1] for v in vertices], color="red", linewidth=3, alpha=0.5)
        elif obs_type == "pillar":
            circle = patches.Circle(obs.get("center"), obs.get("radius"), edgecolor="darkred", facecolor="red", alpha=0.3)
            ax.add_patch(circle)

    # Vẽ Nodes
    node_positions = {}
    for node in layout.get("nodes", []):
        x, y = node["x"], node["y"]
        node_positions[node["node_id"]] = (x, y)
        marker = "s" if node.get("type") == "dock" else "p" if node.get("type") == "storage" else "o"
        ax.scatter(x, y, s=80, color="navy" if node.get("type") != "waypoint" else "gray", marker=marker, zorder=5)
        ax.text(x, y + 0.2, node["node_id"], fontsize=8, ha="center", va="bottom", zorder=6,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", boxstyle="round,pad=0.1"))

    # Vẽ Edges đường đi liên kết
    for edge in layout.get("edges", []):
        p1 = node_positions.get(edge.get("start_node_id"))
        p2 = node_positions.get(edge.get("end_node_id"))
        if p1 and p2:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="lightgray", linestyle=":", zorder=1)

    # 2. Khởi tạo đối tượng đại diện cho xe AGV di động
    agv_dots = {}   # {serial: plot_object}
    agv_texts = {}  # {serial: text_object}
    
    # Lấy danh sách các AGV từ tick đầu tiên
    first_tick_agvs = tick_states[0]["agvs"]
    for serial in first_tick_agvs.keys():
        dot, = ax.plot([], [], marker="o", color="blue", markersize=10, zorder=10)
        txt = ax.text(0, 0, "", fontsize=9, color="blue", weight="bold", zorder=11,
                      bbox=dict(facecolor="white", alpha=0.8, edgecolor="blue", boxstyle="round,pad=0.2"))
        agv_dots[serial] = dot
        agv_texts[serial] = txt

    time_text = ax.text(0.02, 0.95, "", transform=ax.transAxes, fontsize=12, weight="bold",
                        bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"))

    def init():
        for dot in agv_dots.values():
            dot.set_data([], [])
        for txt in agv_texts.values():
            txt.set_text("")
        time_text.set_text("Time: 0.0s")
        return list(agv_dots.values()) + list(agv_texts.values()) + [time_text]

    def update(frame_idx):
        frame = tick_states[frame_idx]
        elapsed = frame["elapsed_time"]
        agvs_data = frame["agvs"]

        artists = []
        for serial, sim_state in agvs_data.items():
            pos = sim_state.get("agvPosition", {})
            x = pos.get("x", 0.0)
            y = pos.get("y", 0.0)
            
            # Cập nhật vị trí dấu chấm xe
            if serial in agv_dots:
                agv_dots[serial].set_data([x], [y])
                artists.append(agv_dots[serial])
            
            # Cập nhật thông tin pin và trạng thái của xe
            bat = sim_state.get("batteryState", {}).get("batteryCharge", 100.0)
            is_driving = sim_state.get("driving", False)
            status_str = "MOVING" if is_driving else "IDLE"
            
            # Kiểm tra nếu xe đang thực hiện action nào
            action_states = sim_state.get("actionStates", [])
            active_actions = [a for a in action_states if a.get("actionStatus") == "RUNNING"]
            if active_actions:
                status_str = active_actions[0].get("actionType", "ACTION").upper()

            if serial in agv_texts:
                agv_texts[serial].set_position((x, y + 0.35))
                agv_texts[serial].set_text(f"{serial}\nHP: {bat:.1f}%\n[{status_str}]")
                artists.append(agv_texts[serial])
                
        time_text.set_text(f"Time: {elapsed:.1f}s")
        artists.append(time_text)
        return artists

    ani = animation.FuncAnimation(
        fig, update, frames=len(tick_states), init_func=init,
        interval=50, blit=True, repeat=False
    )
    
    plt.show()

if __name__ == "__main__":
    # Tìm thư mục kết quả mới nhất nếu không truyền tham số
    results_dir = "results"
    subdirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, d))]
    latest_run = max(subdirs, key=os.path.getmtime) if subdirs else None

    parser = argparse.ArgumentParser(description="Replay AGV Benchmark Simulation Run")
    parser.add_argument(
        "--run_dir", 
        type=str, 
        default=latest_run,
        help="Đường dẫn đến thư mục kết quả test (ví dụ: results/gemini-2.5-flash_...)"
    )
    args = parser.parse_args()

    if not args.run_dir:
        print("Error: Thư mục kết quả trống và không tìm thấy lượt chạy nào trước đó trong results/")
    else:
        print(f"Loading run results from: {args.run_dir}")
        layout, tick_states = load_benchmark_run(args.run_dir)
        play_animation(layout, tick_states)
