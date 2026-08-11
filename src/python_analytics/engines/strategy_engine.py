class StrategyManager:
    def __init__(self):
        """
        Initialises the Strategy Manager to route validated signals 
        to the appropriate algorithmic execution module[cite: 2].
        """
        self.active_module = "None"

    # def _trend_following_module(self, market_data: dict) -> dict:
    #     """
    #     Executes logic for established trends[cite: 2].
    #     Buys pullbacks in bull trends, sells rallies in bear trends.
    #     """
    #     direction = market_data.get("Trend Direction", "Unknown")
    #     strength = market_data.get("Trend Strength Score", 0)
        
    #     # Example execution logic: Only enter if trend strength remains above 50
    #     if strength > 50:
    #         action = "BUY" if direction == "Bullish" else "SELL"
    #         return {"Action": action, "Strategy": "Trend-Following", "Target Multiplier": 3.0}
        
    #     return {"Action": "HOLD", "Strategy": "Trend-Following"}
    def _trend_following_module(self, market_data: dict) -> dict:
        """
        Executes logic for established trends.
        """
        # Updated keys to match ConfidenceEngine output
        strength = market_data.get("Trend Score", 0)
        confidence = market_data.get("Final Confidence", 0)
        
        # Trigger trade if Trend Score or Final Confidence passes the filter
        if strength > 50 or confidence > 50:
            # Defaulting to BUY for trend direction if unassigned
            return {"Action": "BUY", "Strategy": "Trend-Following", "Target Multiplier": 2.0}
        
        return {"Action": "HOLD", "Strategy": "Trend-Following"}

    def _mean_reversion_module(self, market_data: dict) -> dict:
        """
        Executes logic for ranging and highly mean-reverting environments[cite: 2].
        Fades the extremes of the structural range.
        """
        # Example execution logic: Buy when price sweeps Sell-Side Liquidity
        ssl_depth = market_data.get("Sell Side Liquidity", "Low")
        bsl_depth = market_data.get("Buy Side Liquidity", "Low")
        
        if ssl_depth == "High":
            return {"Action": "BUY", "Strategy": "Mean-Reversion", "Target Multiplier": 1.5}
        elif bsl_depth == "High":
            return {"Action": "SELL", "Strategy": "Mean-Reversion", "Target Multiplier": 1.5}
            
        return {"Action": "HOLD", "Strategy": "Mean-Reversion"}

    def _breakout_module(self, market_data: dict) -> dict:
        """
        Executes logic for compression phases anticipating an expansion[cite: 2].
        Places straddle orders or directional stops outside the compression zone.
        """
        # Example execution logic: Prepare for expansion when sweep probability is high
        sweep_prob = float(market_data.get("Sweep Probability", "0%").replace("%", ""))
        
        if sweep_prob > 80.0:
            return {"Action": "PREPARE_BREAKOUT_ORDERS", "Strategy": "Breakout", "Target Multiplier": 5.0}
            
        return {"Action": "HOLD", "Strategy": "Breakout"}

    def route_signal(self, decision_state: dict, mie_data: dict) -> dict:
        """
        Routes the validated market state to the correct execution module[cite: 2].
        """
        is_permitted = decision_state.get("Trading Permitted", False)
        validated_state = decision_state.get("Final Execution State", "Neutral")
        
        if not is_permitted or validated_state == "Neutral":
            self.active_module = "None"
            return {"Action": "FLAT", "Reason": "Decision Engine Block"}

        # Route to the Trend-Following module[cite: 2]
        if validated_state in ["Trend", "Weak Trend"]:
            self.active_module = "Trend-Following"
            return self._trend_following_module(mie_data)
            
        # Route to the Mean-Reversion module[cite: 2]
        elif validated_state == "Range":
            self.active_module = "Mean-Reversion"
            return self._mean_reversion_module(mie_data)
            
        # Route to the Breakout module[cite: 2]
        elif validated_state in ["Compression", "Expansion"]:
            self.active_module = "Breakout"
            return self._breakout_module(mie_data)
            
        return {"Action": "FLAT", "Reason": f"Unmapped State: {validated_state}"}

if __name__ == "__main__":
    manager = StrategyManager()
    
    # Simulated inputs from the Decision Engine and Market Intelligence Engine
    mock_decision = {
        "Trading Permitted": True,
        "Final Execution State": "Compression"
    }
    
    mock_mie_data = {
        "Sweep Probability": "85.0%"
    }
    
    print("\n--- Strategy Manager Routing ---")
    order_directive = manager.route_signal(mock_decision, mock_mie_data)
    for key, value in order_directive.items():
        print(f"{key}: {value}")