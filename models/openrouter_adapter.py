import time
import json
import os
import requests
from typing import Dict, List, Any, Optional
from models.base_adapter import BaseModelAdapter, ModelResponse

class OpenRouterModelAdapter(BaseModelAdapter):
    """Adapter cho các LLMs chạy qua OpenRouter API (hỗ trợ các model miễn phí)"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "qwen/qwen-2.5-coder-32b:free"):
        # Nạp API key từ môi trường nếu không truyền vào
        if not api_key:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("OPENROUTER_API_KEY")
            
        super().__init__(api_key)
        self.model_name = model_name

    def generate_orders(
        self,
        factory_layout: Dict[str, Any],
        agv_states: List[Dict[str, Any]],
        transport_requests: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> ModelResponse:
        
        if not self.api_key:
            return ModelResponse(
                status="FAILED",
                orders={},
                raw_response="",
                latency_ms=0.0,
                error_message="OpenRouter API Key is missing. Please set OPENROUTER_API_KEY in .env."
            )

        # 1. Xây dựng prompt điều khiển hệ thống
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

        # 2. Gửi request tới OpenRouter
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AGV Reasoning Simulator",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }

        start_time = time.time()
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                return ModelResponse(
                    status="FAILED",
                    orders={},
                    raw_response=response.text,
                    latency_ms=latency_ms,
                    error_message=f"OpenRouter API returned status {response.status_code}: {response.text}"
                )
                
            res_json = response.json()
            raw_text = res_json["choices"][0]["message"]["content"]
            
            # Làm sạch định dạng markdown code blocks nếu có
            clean_text = raw_text.strip()
            # Bỏ phần suy nghĩ của DeepSeek R1 nếu xuất dưới thẻ <think>...</think>
            if "<think>" in clean_text and "</think>" in clean_text:
                clean_text = clean_text.split("</think>")[-1].strip()
                
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            parsed_data = json.loads(clean_text)
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
