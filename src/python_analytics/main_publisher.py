# import zmq
# import json
# import time

# class ZeroMQPublisher:
#     def __init__(self, port: int = 5555):
#         """Initialises the ZeroMQ publisher socket to broadcast execution signals."""
#         self.context = zmq.Context()
#         self.socket = self.context.socket(zmq.PUB)
#         self.socket.bind(f"tcp://127.0.0.1:{port}")
#         print(f"MIE Core broadcasting on port {port}...")

#     def broadcast_signal(self, payload: dict):
#         """Converts the signal to JSON and publishes it to the C++ subscriber."""
#         message = json.dumps(payload)
#         self.socket.send_string(f"TRADE_SIGNAL {message}")
#         print(f"Broadcasted: {message}")

# if __name__ == "__main__":
#     publisher = ZeroMQPublisher()
    
#     # Simulating the output from your Strategy Manager
#     mock_signal = {
#         "Action": "BUY",
#         "Strategy": "Trend-Following",
#         "Asset": "SPY",
#         "Confidence": 85.0,
#         "Target Multiplier": 3.0,
#         "Timestamp": time.time()
#     }
    
#     # In a live loop, this fires whenever the MIE generates a validated signal
#     while True:
#         publisher.broadcast_signal(mock_signal)
#         time.sleep(5) # Simulating a 5-second tick delay

import sys
import os
import time
import json
import zmq

# Ensure package imports resolve cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data
from src.python_analytics.engines.confidence_engine import ConfidenceEngine
from src.python_analytics.engines.decision_engine import DecisionEngine
from src.python_analytics.engines.strategy_engine import StrategyManager
from src.python_analytics.analysers.risk_intelligence import RiskIntelligence

class MIEPublisher:
    def __init__(self, port: int = 5555):
        """Initialises ZeroMQ socket for broadcasting live execution signals."""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://127.0.0.1:{port}")
        
        # Core engines
        self.decision_engine = DecisionEngine(confidence_threshold=45.0, confirmation_bars=2)
        self.strategy_manager = StrategyManager()
        
        print(f"[MIE Core] Broadcasting real-time signals on tcp://127.0.0.1:{port}")

    def run_tick_loop(self, symbol: str = "SPY", interval_seconds: int = 10):
        """Simulates real-time market data ingestion and signal broadcasting."""
        print(f"[MIE Core] Starting live tick engine for {symbol}...\n")
        
        while True:
            try:
                # Fetch recent historical window
                df = fetch_sandbox_data(symbol=symbol, period="5d", interval="15m")
                
                # Compute MIE outputs
                conf_engine = ConfidenceEngine(df)
                risk_intel = RiskIntelligence(df)
                
                confidence_output = conf_engine.evaluate_latest()
                risk_output = risk_intel.evaluate_latest()
                
                final_conf = confidence_output.get("Final Confidence", 0)
                
                # Evaluate Decision Engine & Strategy Routing
                decision = self.decision_engine.evaluate_signal(
                    raw_phase="Trend",
                    confidence_score=final_conf
                )
                
                directive = self.strategy_manager.route_signal(decision, confidence_output)
                
                # Construct JSON Payload for C++ Execution Layer
                payload = {
                    "symbol": symbol,
                    "action": directive.get("Action", "FLAT"),
                    "strategy": directive.get("Strategy", "None"),
                    "confidence": final_conf,
                    "environmental_risk": risk_output.get("Total Environmental Risk", 0),
                    "timestamp": time.time()
                }
                
                # Broadcast signal via ZeroMQ
                msg_str = json.dumps(payload)
                self.socket.send_string(f"TRADE_SIGNAL {msg_str}")
                
                print(f"[{time.strftime('%H:%M:%S')}] Broadcasted -> Action: {payload['action']} | Confidence: {payload['confidence']}/100")
                
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n[MIE Core] Shutting down live publisher.")
                break
            except Exception as e:
                print(f"[Error] Tick cycle exception: {e}")
                time.sleep(5)

if __name__ == "__main__":
    publisher = MIEPublisher(port=5555)
    publisher.run_tick_loop(symbol="SPY", interval_seconds=10)