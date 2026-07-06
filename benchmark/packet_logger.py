import json
import os
from datetime import datetime

class PacketLogger:
    """Ghi lại tất cả các gói tin và sự kiện vào file JSONL"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.log_file_path = os.path.join(output_dir, "packet_log.jsonl")
        self.log_file = open(self.log_file_path, "a", encoding="utf-8")

    def log_event(self, event_type: str, direction: str, data: dict, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": event_type,
            "direction": direction,
            "data": data
        }
        log_entry.update(kwargs)
        self.log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        self.log_file.flush()

    def close(self):
        if self.log_file and not self.log_file.closed:
            self.log_file.close()
