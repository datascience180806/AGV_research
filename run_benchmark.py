import argparse
import os
import glob
from dotenv import load_dotenv
from models import GeminiModelAdapter
from benchmark.runner import BenchmarkRunner

def main():
    # Load các biến môi trường từ file .env
    load_dotenv()

    parser = argparse.ArgumentParser(description="AGV Physical Model Reasoning Benchmark Engine")
    parser.add_argument(
        "--scenario", 
        type=str, 
        default="scenarios/level_1_basic/scenario_001.json",
        help="Đường dẫn đến file kịch bản JSON cụ thể"
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3, 4],
        help="Chạy toàn bộ kịch bản thuộc một cấp độ cụ thể (1, 2, 3, 4)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Tên mô hình Gemini sử dụng (mặc định: gemini-2.5-flash)"
    )
    args = parser.parse_args()

    # Khởi tạo adapter cho model tương ứng
    is_openrouter = args.model.startswith("openrouter/") or args.model.endswith(":free")
    is_qwen_cloud = args.model.startswith("qwen-")
    is_groq = args.model.startswith("groq-") or args.model in ["llama-3.1-8b-instant", "gemma2-9b-it", "llama-3.3-70b-versatile", "openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3-32b", "qwen/qwen3.6-27b", "meta-llama/llama-4-scout-17b-16e-instruct"]
    is_hf = "/" in args.model and not is_openrouter and not is_groq and not is_qwen_cloud
    
    if is_openrouter:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("Error: OPENROUTER_API_KEY không tìm thấy trong file .env hoặc biến môi trường.")
            return
        from models import OpenRouterModelAdapter
        adapter = OpenRouterModelAdapter(api_key=api_key, model_name=args.model)
    elif is_qwen_cloud:
        api_key = os.getenv("QWEN_API_KEY") or os.getenv("ALIBABA_CLOUD_MODEL_API_KEY")
        if not api_key:
            print("Error: QWEN_API_KEY hoặc ALIBABA_CLOUD_MODEL_API_KEY không tìm thấy trong file .env hoặc biến môi trường.")
            return
        from models import QwenModelAdapter
        adapter = QwenModelAdapter(api_key=api_key, model_name=args.model)
    elif is_groq:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY không tìm thấy trong file .env hoặc biến môi trường.")
            return
        from models import GroqModelAdapter
        adapter = GroqModelAdapter(api_key=api_key, model_name=args.model)
    elif is_hf:
        api_key = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            print("Error: HF_TOKEN hoặc HUGGINGFACE_API_KEY không tìm thấy trong file .env hoặc biến môi trường.")
            return
        from models import HuggingFaceModelAdapter
        adapter = HuggingFaceModelAdapter(api_key=api_key, model_name=args.model)
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY không tìm thấy trong file .env hoặc biến môi trường.")
            return
        from models import GeminiModelAdapter
        adapter = GeminiModelAdapter(api_key=api_key, model_name=args.model)
        
    runner = BenchmarkRunner(model_adapter=adapter)

    # Lập danh sách kịch bản để chạy
    scenarios_to_run = []
    if args.level:
        level_map = {
            1: "level_1_basic",
            2: "level_2_intermediate",
            3: "level_3_advanced",
            4: "level_4_expert"
        }
        level_dir = level_map[args.level]
        scenarios_to_run = glob.glob(f"scenarios/{level_dir}/*.json")
        print(f"Chạy toàn bộ {len(scenarios_to_run)} kịch bản thuộc Level {args.level}...")
    else:
        if os.path.exists(args.scenario):
            scenarios_to_run = [args.scenario]
        else:
            print(f"Error: Không tìm thấy file kịch bản tại: {args.scenario}")
            return

    # Khởi chạy các kịch bản và in báo cáo
    print("=" * 60)
    print(" RUNNING BENCHMARK EVALUATION ")
    print("=" * 60)

    results = []
    for sc_path in scenarios_to_run:
        print(f"\n[Scenario] Running: {os.path.basename(sc_path)}")
        metrics = runner.run_scenario(sc_path)
        results.append((sc_path, metrics))

    # In báo cáo tóm tắt trên Console
    print("\n" + "=" * 60)
    print(" BENCHMARK REPORT SUMMARY ")
    print("=" * 60)
    
    success_count = 0
    for sc_path, metrics in results:
        status_str = "SUCCESS" if metrics.success else f"FAILED ({metrics.failure_reason})"
        if metrics.success:
            success_count += 1
            
        print(f"- {os.path.basename(sc_path)}:")
        print(f"  Status            : {status_str}")
        print(f"  API Latency       : {metrics.model_latency_ms:.1f} ms")
        if metrics.success or metrics.failure_reason != "invalid_json":
            print(f"  Simulation Time   : {metrics.simulation_time_seconds:.2f} s")
            print(f"  Collisions        : {metrics.collision_count}")
            for agv, bat in metrics.final_battery.items():
                print(f"  Remaining Battery ({agv}): {bat:.2f}%")
        print("-" * 40)

    total = len(results)
    rate = (success_count / total) * 100 if total > 0 else 0
    print(f"\nSUMMARY: Completed {success_count}/{total} scenarios ({rate:.1f}%)")
    print(f"Logs and VDA5050 packets recorded in 'results/' directory.")
    print("=" * 60)

if __name__ == "__main__":
    main()
