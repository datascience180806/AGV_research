---
title: AGV Simulator
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# VDA 5050 Robot Simulator

Python-based simulation environment for robots with VDA 5050 protocol (specifically targeting version 2.0.0). It allows simulating multiple AGVs (Automated Guided Vehicles), sending them orders, and visualizing their movement and status.

## Demo Video
[![IMAGE](images/image.png)](https://youtu.be/wxV-e8J-8gQ)

## Features

* **VDA 5050 v2.0.0 Compliance:** Simulates key aspects of the VDA 5050 protocol including:
    * Connection states (`ONLINE`, `OFFLINE`, `CONNECTION_BROKEN`)
    * Vehicle State (`State`, `AgvPosition`, `ActionState`, etc.)
    * Order processing (`Order`, `Node`, `Edge`)
    * Instant Actions (`InstantActions`, `Action`)
    * Visualization messages (`Visualization`)
* **Multi-Robot Simulation:** Can simulate multiple AGVs concurrently, configured via kịch bản JSON.
* **AI Fleet Coordination Benchmarking:** Evaluates LLMs (Gemini, Llama, Qwen) in generating optimal conflict-free routes and actions under VDA 5050 constraints.
* **Web UI Dashboard:** Interactive frontend displaying real-time simulation runs, layout configurations, obstacle avoidance, and remaining battery levels.
* **CI/CD Integration:** Automated unit tests and Docker image build verification via GitHub Actions.

---

## Directory Structure

```text
vda5050-robot-simulator/
├── .github/workflows/      # CI configuration (automated test & docker build)
├── benchmark/              # Core evaluation engine (runner, metrics logger)
├── factory_layouts/        # Warehouse maps (nodes, edges, walls, charging zones)
├── frontend/               # Web UI visualizer dashboard (index.html)
├── legacy_mqtt/            # Legacy visualizer and MQTT runner scripts
├── models/                 # API adapters (Gemini, Qwen Cloud, Groq, HF, OpenRouter)
├── protocol/               # VDA 5050 protocol data structures (Python dataclasses)
├── scenarios/              # JSON scenarios (Level 1 Basic -> Level 4 Expert)
├── scripts/                # API connection tests and helper utilities
├── tests/                  # Automated unit test suite
├── app.py                  # FastAPI backend server
├── config.py / config.toml # Base simulator configuration files
├── main.py                 # Core AGV state machine and simulator logic
├── run_benchmark.py        # CLI benchmark execution tool
└── requirements.txt        # Python dependency list
```

---

## Setup

1. **Clone & Virtual Environment:**
   ```bash
   git clone git@github.com:datascience180806/AGV_research.git
   cd vda5050-robot-simulator
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **API Credentials:**
   Create a `.env` file in the root directory:
   ```env
   # API Keys for Model Adapters (Fill in what you use)
   GEMINI_API_KEY=your_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   QWEN_API_KEY=your_alibaba_qwen_api_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   HF_TOKEN=your_huggingface_token
   ```

---

## Web Visualizer & Benchmark Tool

This project features a Web-based interactive visualizer dashboard and benchmark suite that runs without needing a local MQTT broker.

1. **Start the Backend API Server:**
   ```bash
   python -m uvicorn app:app --host 127.0.0.1 --port 8000
   ```
   *This runs the FastAPI server at `http://127.0.0.1:8000`. You can access the API documentation at `http://127.0.0.1:8000/docs`.*

2. **Start the Frontend Client:**
   Run a local static web server in the root directory:
   ```bash
   python -m http.server 3000
   ```
   Then, open your browser and navigate to **`http://localhost:3000/frontend/`**.

3. **Run Benchmarks via CLI:**
   You can also run scenarios via command line:
   ```bash
   # Run a single scenario with Gemini 2.5 Flash
   python run_benchmark.py --scenario scenarios/level_1_basic/scenario_001.json --model gemini-2.5-flash
   
   # Run a scenario using Qwen Max Cloud
   python run_benchmark.py --scenario scenarios/level_1_basic/scenario_001.json --model qwen-max
   ```

---

## Running Tests

To run the unit tests locally:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## Docker Deployment

To build and run the backend using Docker:
```bash
# Build the Docker image
docker build -t vda5050-robot-simulator .

# Run the container
docker run -p 7860:7860 vda5050-robot-simulator
```
The FastAPI backend will then be exposed at `http://localhost:7860`.
