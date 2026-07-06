# VDA5050 Robot Simulator

Python-based simulation environment for robots with VDA 5050 protocol (specifically targeting version 2.0.0). It allows simulating multiple AGVs (Automated Guided Vehicles), sending them orders, and visualizing their movement and status via MQTT.

## Demo Video
[![IMAGE](images/image.png)](https://youtu.be/wxV-e8J-8gQ)

## Features

* **VDA 5050 v2.0.0 Compliance:** Simulates key aspects of the VDA 5050 protocol including:
    * Connection states (`ONLINE`, `OFFLINE`, `CONNECTION_BROKEN`)
    * Vehicle State (`State`, `AgvPosition`, `ActionState`, etc.)
    * Order processing (`Order`, `Node`, `Edge`)
    * Instant Actions (`InstantActions`, `Action`)
    * Visualization messages (`Visualization`)
* **Multi-Robot Simulation:** Can simulate multiple AGVs concurrently, configured via `config.toml`.
* **MQTT Communication:** Uses MQTT for communication between the simulator, commander, and potentially other systems.
* **Commander & Visualizer:** Includes a separate script (`commander_visualizer.py`) to:
    * Send `initPosition` instant actions and `Order` commands to simulated robots.
    * Subscribe to `Visualization` topics and display robot positions and paths using Matplotlib.
* **Configurable:** Simulation parameters (MQTT broker details, vehicle properties, simulation speed, robot count, etc.) are managed through a `config.toml` file.
* **Modular Protocol Definitions:** VDA 5050 message structures are defined using Python dataclasses in the `protocol` directory.

## Structure

```vda5050-robot-simulator/
├── config.toml             # Configuration file (Needs to be created)
├── config.py               # Loads configuration from config.toml
├── main.py                 # Main simulator script, runs AGV instances
├── commander_visualizer.py # Sends commands and visualizes robot states
├── mqtt_utils.py           # MQTT connection and topic utilities
├── utils.py                # Helper functions (timestamps, math)
└── protocol/               # VDA5050 protocol message definitions
├── vda5050_common.py   # Common data structures
└── vda_2_0_0/          # VDA 5050 v2.0.0 specific messages
├── vda5050_2_0_0_action.py
├── vda5050_2_0_0_connection.py
├── vda5050_2_0_0_instant_actions.py
├── vda5050_2_0_0_order.py
├── vda5050_2_0_0_state.py
└── vda5050_2_0_0_visualization.py
```

## Setup

1.  **Dependencies:** Install the project dependencies listed in `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
2.  **API Configuration:** Create a `.env` file in the root directory and add your Google Gemini API key:
    ```env
    GEMINI_API_KEY=your_gemini_api_key_here
    ```
3.  **AGV Simulator Configuration:** Create a `config.toml` file in the root directory. Based on `config.py`, it should look something like this:
    ```toml
    [mqtt_broker]
    host = "localhost" # e.g., "localhost" or IP address
    port = "1883" # Default MQTT port
    vda_interface = "uagv"

    [vehicle]
    manufacturer = "YourCompany"
    serial_number = "SimRobot" # Base serial number, index is appended
    vda_version = "2.0.0"
    vda_full_version = "VDA5050_V2.0.0"

    [settings]
    action_time = 2.0   # Time in seconds for simulated actions (e.g., dropOff)
    speed = 0.5         # Simulation speed (units per tick)
    robot_count = 3     # Number of robots to simulate
    state_frequency = 1 # Hz
    visualization_frequency = 10 # Hz
    map_id = "map1"     # Default map ID
    ```

## Web Visualizer & Benchmark Tool (Recommended)

This project features a Web-based interactive visualizer dashboard and benchmark suite that runs without needing a local MQTT broker.

1.  **Start the Backend API Server:**
    ```bash
    python -m uvicorn app:app --host 127.0.0.1 --port 8000
    ```
    *This runs the FastAPI server at `http://127.0.0.1:8000`. You can access the API documentation at `http://127.0.0.1:8000/docs`.*

2.  **Start the Frontend Client:**
    Run a local static web server in the root directory:
    ```bash
    python -m http.server 3000
    ```
    Then, open your browser and navigate to **`http://localhost:3000`**.

3.  **Run Benchmarks via CLI:**
    You can also run scenarios via command line:
    ```bash
    # Run a single scenario
    python run_benchmark.py --scenario scenarios/level_1_basic/scenario_001.json
    
    # Run all scenarios at a specific level
    python run_benchmark.py --level 1
    
    # Playback a recorded benchmark run offline
    python play_benchmark.py
    ```

## Legacy MQTT Simulator Usage (Original)

1.  **Start an MQTT Broker:** Ensure a broker such as [Mosquitto](https://mosquitto.org/) is running.
2.  **Run the Simulator:**
    ```bash
    python main.py
    ```
3.  **Run the Commander/Visualizer:**
    ```bash
    python commander_visualizer.py
    ```

## Structure & How it Works

* **`app.py`**: Web API server (FastAPI) managing layouts, scenarios, benchmark execution, and playback.
* **`index.html`**: Streamlined frontend visualizer displaying layouts, kịch bản, model parameters, and animating AGV paths.
* **`benchmark/`**: Core reasoning evaluation framework that simulates VDA 5050 physics in-memory.
* **`models/`**: AI model adapter layer communicating with the Google GenAI API.
* **`scenarios/`**: Standard JSON task files grouped from Level 1 (Basic) to Level 4 (Expert).
* **`factory_layouts/`**: JSON map layouts containing nodes, edges, obstacles, and zones.
* **`main.py`**: Original simulator managing autonomous AGV connections, state iteration, and order/action processing via MQTT.
