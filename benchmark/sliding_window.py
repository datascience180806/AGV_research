from collections import deque

class SlidingWindowBuffer:
    """Sliding window buffer for telemetry packets (VDA 5050 states + Sensors)"""
    def __init__(self, window_size: int = 15):
        self.window_size = window_size
        self.buffer = deque(maxlen=window_size)

    def push(self, packet: dict):
        """Append a packet to the buffer"""
        self.buffer.append(packet)

    def get_window(self) -> list:
        """Returns the list of packets currently in the window"""
        return list(self.buffer)
