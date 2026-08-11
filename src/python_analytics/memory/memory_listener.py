import sys
import os
import json
import zmq

# Ensure path imports resolve
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.python_analytics.memory.market_memory import MarketMemory

def start_memory_listener(port: int = 5556):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://127.0.0.1:{port}")
    socket.setsockopt_string(zmq.SUBSCRIBE, "TRADE_LOG")

    memory = MarketMemory()
    print(f"[Memory Listener] Listening for C++ execution logs on tcp://127.0.0.1:{port}...")

    while True:
        try:
            raw_msg = socket.recv_string()
            payload_str = raw_msg.replace("TRADE_LOG ", "")
            log_data = json.loads(payload_str)

            print(f"[Memory Listener] Trade Log Intercepted: {log_data}")

            # Prepare database record
            episode_record = {
                "regime": "Trend",
                "start_time": "10:00",
                "end_time": "10:45",
                "duration_bars": log_data.get("duration_bars", 0),
                "max_pullback": 12.0,
                "profit_opportunity": log_data.get("pnl", 0.0),
                "outcome": log_data.get("outcome", "Unknown"),
                "trend_strength": 80.0,
                "momentum": 75.0,
                "volatility": 50.0,
                "compression": 10.0,
                "liquidity": 85.0,
                "confidence": 90.0
            }

            # Log into SQLite/MySQL
            memory.log_episode(episode_record)
            print("[Memory Listener] Logged episode to market_memory.db successfully.\n")

        except KeyboardInterrupt:
            print("\n[Memory Listener] Shutting down.")
            break
        except Exception as e:
            print(f"[Memory Error] Exception processing log: {e}")

if __name__ == "__main__":
    start_memory_listener()