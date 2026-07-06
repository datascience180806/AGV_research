import time
import json
import os
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from models.base_adapter import BaseModelAdapter, ModelResponse

class GeminiModelAdapter(BaseModelAdapter):
    """Adapter cho Google Gemini API sử dụng SDK google-genai mới nhất"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        # Load API key từ môi trường nếu không truyền vào
        if not api_key:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            
        super().__init__(api_key)
        self.model_name = model_name
        self.client = None
        
        if self.api_key:
            # Khởi tạo client của bộ SDK google-genai mới
            self.client = genai.Client(api_key=self.api_key)
        else:
            print("Warning: Gemini API Key is missing. Please set it in .env or pass it to constructor.")

    def generate_orders(
        self,
        factory_layout: Dict[str, Any],
        agv_states: List[Dict[str, Any]],
        transport_requests: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> ModelResponse:
        
        if not self.client:
            return ModelResponse(
                status="FAILED",
                orders={},
                raw_response="",
                latency_ms=0.0,
                error_message="Gemini Client is not configured. Missing API Key."
            )

        # 1. Xây dựng Prompt chi tiết
        system_prompt = (
            "You are the Fleet Management Controller (Master Control) for an Automated Guided Vehicle (AGV) system "
            "operating under the VDA 5050 protocol version 2.0.0.\n\n"
            "Your task is to analyze the factory layout, the current states of the AGVs, and the pending transport requests, "
            "then generate a set of VDA 5050 Orders directing the AGVs to complete the transport requests safely and efficiently.\n\n"
            "CRITICAL PROTOCOL RULES:\n"
            "1. Output format MUST be a valid JSON matching the schema below.\n"
            "2. Each AGV requires an order to move. The order contains a sequence of Nodes and Edges connecting them.\n"
            "3. The sequence_id starts at 1 and increments by 1 for each node/edge in order: Node(seq=1) -> Edge(seq=2) -> Node(seq=3) -> Edge(seq=4) -> Node(seq=5) etc.\n"
            "4. A Node must contain: nodeId, sequenceId, released (boolean), nodePosition (x, y, mapId), and actions (list).\n"
            "5. An Edge must contain: edgeId, sequenceId, released (boolean), startNodeId, endNodeId, and actions (list).\n"
            "6. To pick up or drop off a package, insert an action inside the actions list of the target Node.\n"
            "   - Pickup action format: {\"actionType\": \"pickUp\", \"actionId\": \"<unique_id>\", \"blockingType\": \"HARD\", \"actionParameters\": []}\n"
            "   - Dropoff action format: {\"actionType\": \"dropOff\", \"actionId\": \"<unique_id>\", \"blockingType\": \"HARD\", \"actionParameters\": []}\n"
            "   - Charge action format: {\"actionType\": \"charge\", \"actionId\": \"<unique_id>\", \"blockingType\": \"HARD\", \"actionParameters\": []}\n"
            "7. Ensure path routing respects the connections in the factory layout edges. AGVs can only move from node A to node B if an edge exists connecting them.\n"
            "8. Avoid paths that overlap at the same time to prevent collisions."
        )

        user_content = {
            "factory_layout": factory_layout,
            "agv_states": agv_states,
            "transport_requests": transport_requests,
            "constraints": constraints
        }

        prompt = (
            f"Here is the context of the warehouse environment in JSON:\n"
            f"{json.dumps(user_content, indent=2)}\n\n"
            f"Generate the orders for each AGV. Respond ONLY with a JSON object in this format:\n"
            f"{{\n"
            f"  \"orders\": {{\n"
            f"    \"<agv_serial_number>\": {{\n"
            f"      \"orderId\": \"<unique_order_id>\",\n"
            f"      \"orderUpdateId\": 0,\n"
            f"      \"nodes\": [ ... VDA5050 Nodes ... ],\n"
            f"      \"edges\": [ ... VDA5050 Edges ... ]\n"
            f"    }}\n"
            f"  }}\n"
            f"}}"
        )

        # 2. Thực hiện gọi API Gemini sử dụng SDK mới
        start_time = time.time()
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json"
                )
            )
            
            latency_ms = (time.time() - start_time) * 1000
            raw_text = response.text
            
            # Parse kết quả để kiểm tra tính hợp lệ của JSON
            parsed_data = json.loads(raw_text)
            orders = parsed_data.get("orders", {})
            
            return ModelResponse(
                status="SUCCESS",
                orders=orders,
                raw_response=raw_text,
                latency_ms=latency_ms
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ModelResponse(
                status="FAILED",
                orders={},
                raw_response=locals().get("raw_text", ""),
                latency_ms=latency_ms,
                error_message=str(e)
            )
