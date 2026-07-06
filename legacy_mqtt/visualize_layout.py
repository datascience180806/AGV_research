import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def load_layout(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def plot_layout(layout_data):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Set dimensions
    dims = layout_data.get("dimensions", {"width": 15.0, "height": 15.0})
    ax.set_xlim(-1, dims["width"] + 1)
    ax.set_ylim(-1, dims["height"] + 1)
    ax.set_aspect('equal')
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title(f"Factory Layout Preview: {layout_data.get('layout_name', 'Unknown')}", fontsize=14, fontweight="bold")
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")

    # 1. Draw Zones (semi-transparent filled rectangles)
    for zone in layout_data.get("zones", []):
        bounds = zone.get("bounds", {})
        x_min = bounds.get("x_min", 0.0)
        y_min = bounds.get("y_min", 0.0)
        x_max = bounds.get("x_max", 0.0)
        y_max = bounds.get("y_max", 0.0)
        
        width = x_max - x_min
        height = y_max - y_min
        
        # Color code based on type
        zone_type = zone.get("type", "general")
        color = "green"
        if zone_type == "charging":
            color = "yellow"
        elif zone_type == "restricted":
            color = "orange"
        elif zone_type == "assembly":
            color = "purple"
            
        rect = patches.Rectangle((x_min, y_min), width, height, linewidth=1, 
                                 edgecolor=color, facecolor=color, alpha=0.15, label=f"Zone: {zone['zone_id']}")
        ax.add_patch(rect)
        ax.text(x_min + 0.1, y_max - 0.4, f"{zone['zone_id']} ({zone_type})", fontsize=8, color=color, weight="bold")

    # 2. Draw Obstacles (solid grey / red boundaries)
    for obs in layout_data.get("obstacles", []):
        obs_type = obs.get("type", "")
        if obs_type == "wall":
            # vertices list
            vertices = obs.get("vertices", [])
            if len(vertices) >= 2:
                # If closed shape
                if vertices[0] == vertices[-1] or len(vertices) > 2:
                    poly = patches.Polygon(vertices, closed=True, linewidth=2, 
                                           edgecolor="darkred", facecolor="red", alpha=0.3, label="Obstacle (Wall)")
                    ax.add_patch(poly)
                else:
                    # Line wall
                    x_val = [v[0] for v in vertices]
                    y_val = [v[1] for v in vertices]
                    ax.plot(x_val, y_val, color="red", linewidth=4, alpha=0.7, label="Wall obstacle")
        elif obs_type == "pillar":
            center = obs.get("center", [0.0, 0.0])
            radius = obs.get("radius", 0.5)
            circle = patches.Circle(center, radius, linewidth=2, edgecolor="darkred", 
                                    facecolor="red", alpha=0.4, label="Pillar obstacle")
            ax.add_patch(circle)

    # Map node IDs to positions for edge plotting
    node_positions = {}
    for node in layout_data.get("nodes", []):
        node_positions[node["node_id"]] = (node["x"], node["y"])

    # 3. Draw Edges (dashed lines connecting nodes)
    for edge in layout_data.get("edges", []):
        start_id = edge.get("start_node_id")
        end_id = edge.get("end_node_id")
        if start_id in node_positions and end_id in node_positions:
            p1 = node_positions[start_id]
            p2 = node_positions[end_id]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="blue", linestyle="--", linewidth=1.5, alpha=0.6)
            # Draw an arrowhead to show direction
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            ax.annotate("", xy=(p2[0] - dx*0.2, p2[1] - dy*0.2), xytext=(p1[0] + dx*0.2, p1[1] + dy*0.2),
                        arrowprops=dict(arrowstyle="->", color="blue", lw=1.5, alpha=0.6))

    # 4. Draw Nodes (circles with labels)
    for node in layout_data.get("nodes", []):
        x, y = node["x"], node["y"]
        node_type = node.get("type", "waypoint")
        
        # Style based on node type
        marker = "o"
        color = "blue"
        size = 80
        if node_type == "dock":
            color = "darkgreen"
            marker = "s"
            size = 100
        elif node_type == "storage":
            color = "navy"
            marker = "p"
            size = 100
            
        ax.scatter(x, y, s=size, color=color, marker=marker, zorder=5)
        ax.text(x, y + 0.2, f"{node['node_id']} ({node_type})", fontsize=9, 
                ha="center", va="bottom", weight="bold", zorder=6,
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", boxstyle="round,pad=0.2"))

    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Visualize Factory Layout JSON")
    parser.add_argument("--layout", type=str, default="factory_layouts/simple_warehouse.json", 
                        help="Path to the layout JSON file")
    args = parser.parse_args()
    
    layout = load_layout(args.layout)
    if layout:
        plot_layout(layout)
