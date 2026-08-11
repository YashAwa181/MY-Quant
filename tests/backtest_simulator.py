import sys
import os
import pandas as pd
import numpy as np

# Append src/ to Python path to ensure module imports resolve correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data
from src.python_analytics.engines.confidence_engine import ConfidenceEngine
from src.python_analytics.engines.decision_engine import DecisionEngine
from src.python_analytics.engines.strategy_engine import StrategyManager
from src.python_analytics.engines.risk_allocator import RiskAllocator
from src.python_analytics.analysers.risk_intelligence import RiskIntelligence

class BacktestSimulator:
    def __init__(self, symbol: str = "SPY", initial_capital: float = 100000.0, min_bars: int = 60):
        """
        Initialises the Event-Driven Backtesting Simulator.
        
        :param symbol: Asset ticker to test.
        :param initial_capital: Starting portfolio balance in USD/GBP.
        :param min_bars: Minimum warm-up period required for rolling indicators.
        """
        self.symbol = symbol
        self.capital = initial_capital
        self.starting_capital = initial_capital
        self.min_bars = min_bars
        
        # Performance Tracking
        self.trades = []
        self.equity_curve = []
        self.active_trade = None

    def run(self, period: str = "60d", interval: str = "15m"):
        """Executes the bar-by-bar simulation backtest loop."""
        print(f"\n--- Loading Historical Data for {self.symbol} ({period}, {interval}) ---")
        full_df = fetch_sandbox_data(symbol=self.symbol, period=period, interval=interval)
        
        if len(full_df) < self.min_bars:
            print("Error: Insufficient historical data for backtesting.")
            return

        decision_engine = DecisionEngine(confidence_threshold=45.0, confirmation_bars=2)
        strategy_manager = StrategyManager()
        risk_allocator = RiskAllocator(account_balance=self.capital)

        print(f"Beginning simulation across {len(full_df) - self.min_bars} bars...\n")

        # Bar-by-bar loop (Simulates live time progression)
        for i in range(self.min_bars, len(full_df)):
            # Slice historical dataframe up to the current bar (no look-ahead bias)
            df_slice = full_df.iloc[:i].copy()
            current_bar = df_slice.iloc[-1]
            current_price = current_bar['close']
            timestamp = df_slice.index[-1]

            # 1. Run MIE Core Engines
            confidence_engine = ConfidenceEngine(df_slice)
            risk_intel = RiskIntelligence(df_slice)
            
            confidence_output = confidence_engine.evaluate_latest()
            risk_output = risk_intel.evaluate_latest()
            
            final_confidence = confidence_output.get("Final Confidence", 0)
            total_risk_threat = risk_output.get("Total Environmental Risk", 0)
            
            # 2. Evaluate Decision Engine & Strategy Manager
            decision = decision_engine.evaluate_signal(
                raw_phase="Trend", # Simplified for backtest runner
                confidence_score=final_confidence
            )
            
            directive = strategy_manager.route_signal(decision, confidence_output)
            action = directive.get("Action", "FLAT")

            # 3. Simulate Trade Lifecycle & Order Execution
            if self.active_trade is None and action in ["BUY", "SELL"]:
                atr = current_bar['high'] - current_bar['low'] # Localized ATR proxy
                allocation = risk_allocator.calculate_position(
                    confidence=final_confidence,
                    risk_threat=total_risk_threat,
                    atr=atr if atr > 0 else 1.0
                )

                if allocation.get("Status") == "APPROVED":
                    stop_dist = allocation["Stop Loss Distance"]
                    sl_price = current_price - stop_dist if action == "BUY" else current_price + stop_dist
                    
                    self.active_trade = {
                        "entry_time": timestamp,
                        "action": action,
                        "entry_price": current_price,
                        "sl": sl_price,
                        "units": allocation["Units"],
                        "risk_capital": allocation["Allocated Capital Risk"]
                    }

            # 4. Manage Open Trade Exits
            elif self.active_trade is not None:
                entry = self.active_trade["entry_price"]
                sl = self.active_trade["sl"]
                units = self.active_trade["units"]
                trade_dir = self.active_trade["action"]

                # Check Stop Loss Violation
                hit_sl = (trade_dir == "BUY" and current_bar['low'] <= sl) or \
                         (trade_dir == "SELL" and current_bar['high'] >= sl)

                if hit_sl:
                    pnl = -self.active_trade["risk_capital"]
                    self.capital += pnl
                    self.trades.append({
                        "entry": entry,
                        "exit": sl,
                        "pnl": pnl,
                        "result": "LOSS"
                    })
                    self.active_trade = None

                # Simple Take Profit Condition (2x Risk-to-Reward)
                else:
                    target_dist = abs(entry - sl) * 2.0
                    hit_tp = (trade_dir == "BUY" and current_bar['high'] >= entry + target_dist) or \
                             (trade_dir == "SELL" and current_bar['low'] <= entry - target_dist)

                    if hit_tp:
                        pnl = self.active_trade["risk_capital"] * 2.0
                        self.capital += pnl
                        self.trades.append({
                            "entry": entry,
                            "exit": entry + target_dist if trade_dir == "BUY" else entry - target_dist,
                            "pnl": pnl,
                            "result": "WIN"
                        })
                        self.active_trade = None

            self.equity_curve.append(self.capital)

        self._generate_performance_report()

    def _generate_performance_report(self):
        """Calculates and outputs key quantitative performance metrics."""
        total_trades = len(self.trades)
        if total_trades == 0:
            print("Backtest Complete: No trades were executed.")
            return

        wins = [t for t in self.trades if t["result"] == "WIN"]
        losses = [t for t in self.trades if t["result"] == "LOSS"]
        
        win_rate = (len(wins) / total_trades) * 100
        net_profit = self.capital - self.starting_capital
        return_pct = (net_profit / self.starting_capital) * 100

        # Calculate Max Drawdown
        equity_series = pd.Series(self.equity_curve)
        peak = equity_series.cummax()
        drawdown = (equity_series - peak) / peak
        max_drawdown_pct = drawdown.min() * 100

        print("=" * 45)
        print("          BACKTEST PERFORMANCE REPORT         ")
        print("=" * 45)
        print(f"Initial Balance:    ${self.starting_capital:,.2f}")
        print(f"Final Balance:      ${self.capital:,.2f}")
        print(f"Net Profit:         ${net_profit:,.2f} ({return_pct:.2f}%)")
        print(f"Total Trades:       {total_trades}")
        print(f"Win Rate:           {win_rate:.1f}%")
        print(f"Max Drawdown:       {max_drawdown_pct:.2f}%")
        print("=" * 45)

if __name__ == "__main__":
    simulator = BacktestSimulator(symbol="SPY", initial_capital=100000.0)
    simulator.run(period="60d", interval="15m")