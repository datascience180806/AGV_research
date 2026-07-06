import os
import glob
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
from models import GeminiModelAdapter, HuggingFaceModelAdapter, OpenRouterModelAdapter, GroqModelAdapter, QwenModelAdapter
from benchmark.runner import BenchmarkRunner

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AGV Reasoning Benchmark API",
    description="Backend API for running and analyzing AGV Reasoning Benchmarks",
    version="1.0.0"
)

# Enable CORS for local static HTML access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BenchmarkRunRequest(BaseModel):
    model_name: str
    scenario_path: str

@app.get("/")
def read_root():
    return {"status": "online", "service": "AGV Simulator Benchmark Server"}

@app.get("/api/layouts")
def get_layouts():
    """Lấy danh sách các sơ đồ mặt bằng có sẵn"""
    layouts_dir = "factory_layouts"
    if not os.path.exists(layouts_dir):
        return []
    
    layouts = []
    for file_path in glob.glob(os.path.join(layouts_dir, "*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                layouts.append({
                    "layout_id": data.get("layout_id"),
                    "layout_name": data.get("layout_name"),
                    "width": data.get("dimensions", {}).get("width", 0),
                    "height": data.get("dimensions", {}).get("height", 0)
                })
        except Exception:
            continue
    return layouts

@app.get("/api/scenarios")
def get_scenarios():
    """Lấy danh sách các kịch bản kiểm thử, gom từ Level 1 đến Level 4"""
    scenarios_dir = "scenarios"
    scenarios = []
    
    if not os.path.exists(scenarios_dir):
        return []

    # Quét qua các thư mục con cấp độ
    levels = ["level_1_basic", "level_2_intermediate", "level_3_advanced", "level_4_expert"]
    for idx, lvl in enumerate(levels, 1):
        lvl_path = os.path.join(scenarios_dir, lvl)
        if not os.path.exists(lvl_path):
            continue
        for file_path in glob.glob(os.path.join(lvl_path, "*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    scenarios.append({
                        "scenario_id": data.get("scenario_id"),
                        "scenario_name": data.get("scenario_name"),
                        "level": idx,
                        "level_name": lvl,
                        "description": data.get("description"),
                        "factory_layout": data.get("factory_layout"),
                        "file_path": file_path.replace("\\", "/")
                    })
            except Exception:
                continue
    return scenarios

@app.post("/api/benchmark/run")
def run_benchmark(req: BenchmarkRunRequest):
    """Khởi chạy thử nghiệm một kịch bản với model chỉ định"""
    is_openrouter = req.model_name.startswith("openrouter/") or req.model_name.endswith(":free")
    is_qwen_cloud = req.model_name.startswith("qwen-")
    is_groq = req.model_name.startswith("groq-") or req.model_name in ["llama-3.1-8b-instant", "gemma2-9b-it", "llama-3.3-70b-versatile", "openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3-32b", "qwen/qwen3.6-27b", "meta-llama/llama-4-scout-17b-16e-instruct"]
    is_hf = "/" in req.model_name and not is_openrouter and not is_groq and not is_qwen_cloud
    
    if is_openrouter:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY is not set in environment variables.")
    elif is_qwen_cloud:
        api_key = os.getenv("QWEN_API_KEY") or os.getenv("ALIBABA_CLOUD_MODEL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="QWEN_API_KEY or ALIBABA_CLOUD_MODEL_API_KEY is not set in environment variables.")
    elif is_groq:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set in environment variables.")
    elif is_hf:
        api_key = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="HF_TOKEN or HUGGINGFACE_API_KEY is not set in environment variables.")
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in environment variables.")

    # Kiểm tra kịch bản có tồn tại hay không
    if not os.path.exists(req.scenario_path):
        raise HTTPException(status_code=404, detail=f"Scenario file not found at: {req.scenario_path}")

    try:
        # Khởi tạo model tương ứng và runner
        if is_openrouter:
            adapter = OpenRouterModelAdapter(api_key=api_key, model_name=req.model_name)
        elif is_qwen_cloud:
            adapter = QwenModelAdapter(api_key=api_key, model_name=req.model_name)
        elif is_groq:
            adapter = GroqModelAdapter(api_key=api_key, model_name=req.model_name)
        elif is_hf:
            adapter = HuggingFaceModelAdapter(api_key=api_key, model_name=req.model_name)
        else:
            adapter = GeminiModelAdapter(api_key=api_key, model_name=req.model_name)
            
        runner = BenchmarkRunner(model_adapter=adapter)
        
        # Chạy giả lập và ghi nhận kết quả
        metrics = runner.run_scenario(req.scenario_path)
        
        # Tìm thư mục kết quả mới nhất được tạo ra để lấy run_id
        run_id = None
        results_dir = "results"
        if os.path.exists(results_dir):
            subdirs = [d for d in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, d))]
            matching_dirs = [d for d in subdirs if d.endswith(metrics.scenario_id)]
            if matching_dirs:
                run_id = max(matching_dirs, key=lambda d: os.path.getmtime(os.path.join(results_dir, d)))
        
        res_dict = metrics.to_dict()
        res_dict["run_id"] = run_id
        return res_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@app.get("/api/results")
def get_results():
    """Lấy lịch sử danh sách toàn bộ các kết quả chạy benchmark"""
    results_dir = "results"
    if not os.path.exists(results_dir):
        return []

    runs = []
    subdirs = [d for d in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, d))]
    for run_id in subdirs:
        report_path = os.path.join(results_dir, run_id, "benchmark_report.json")
        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                    # Lấy thời gian sửa đổi thư mục làm timestamp chạy
                    folder_mtime = os.path.getmtime(os.path.join(results_dir, run_id))
                    report_data["run_id"] = run_id
                    report_data["timestamp"] = folder_mtime
                    runs.append(report_data)
            except Exception:
                continue
    # Sắp xếp các lượt chạy mới nhất lên đầu
    runs.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
    return runs

@app.get("/api/results/{run_id}/playback")
def get_playback(run_id: str):
    """Cung cấp chuỗi di chuyển từng tick của một lần chạy để render animation trên frontend"""
    log_path = os.path.join("results", run_id, "packet_log.jsonl")
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Run directory or packet log not found.")

    layout = None
    tick_states = []
    all_events = []

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                all_events.append(entry)
                
                if entry.get("type") == "layout_loaded":
                    layout = entry.get("data")
                elif entry.get("type") == "sim_tick_state":
                    tick_states.append({
                        "elapsed_time": entry.get("elapsed_time", 0.0),
                        "agvs": entry.get("data", {})
                    })
        return {
            "run_id": run_id,
            "layout": layout,
            "playback_ticks": tick_states,
            "all_events": all_events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read playback logs: {str(e)}")
