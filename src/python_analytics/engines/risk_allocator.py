class RiskAllocator:
    def __init__(self, account_balance: float, max_daily_loss_pct: float = 3.0):
        """
        Initialises the Risk Engine to govern capital allocation and protection.
        """
        self.account_balance = account_balance
        self.max_daily_loss = account_balance * (max_daily_loss_pct / 100.0)
        self.current_daily_loss = 0.0

    def calculate_position(self, confidence: float, risk_threat: float, atr: float) -> dict:
        """
        Calculates dynamic lot sizing and ATR-based stops.
        """
        # Maximum Drawdown Protection / Daily Loss Limits
        if self.current_daily_loss >= self.max_daily_loss:
            return {"Status": "REJECTED", "Reason": "Daily Loss Limit Reached"}

        # Base risk is 1% of account balance
        base_risk_amount = self.account_balance * 0.01

        # Dynamic Lot Sizing: Scale risk up/down based on MIE Confidence and Risk Threat[cite: 2]
        confidence_multiplier = confidence / 100.0
        threat_discount = (100 - risk_threat) / 100.0
        
        adjusted_risk_amount = base_risk_amount * confidence_multiplier * threat_discount
        
        # ATR-based stop loss distance (e.g., 1.5x ATR)[cite: 2]
        stop_loss_distance = atr * 1.5
        
        # Calculate theoretical unit size
        units = adjusted_risk_amount / stop_loss_distance if stop_loss_distance > 0 else 0

        return {
            "Status": "APPROVED",
            "Allocated Capital Risk": round(adjusted_risk_amount, 2),
            "Units": round(units, 4),
            "Stop Loss Distance": round(stop_loss_distance, 4)
        }


class TradeManager:
    def __init__(self):
        """
        Initialises the Trade Manager to handle live positions, trailing stops, 
        partial profit-taking, and time-based exits[cite: 2].
        """
        self.open_positions = {}

    def manage_trade(self, trade_id: str, current_price: float, entry_price: float, 
                     initial_sl: float, target_price: float, time_in_trade_bars: int) -> dict:
        """
        Dynamically adjusts open orders based on price action[cite: 2].
        """
        # Calculate current floating profit percentage
        price_travel = abs(current_price - entry_price)
        distance_to_target = abs(target_price - entry_price)
        progress_pct = (price_travel / distance_to_target) * 100 if distance_to_target > 0 else 0

        # 1. Time-Based Exits[cite: 2]
        # If the trade has stagnated for too long, close it to free up capital
        if time_in_trade_bars > 48: 
            return {"Action": "CLOSE_POSITION", "Reason": "Time-Based Exit"}

        # 2. Partial Profit-Taking[cite: 2]
        # Secure 50% of the position if price reaches 75% of the target
        if progress_pct >= 75.0 and not self.open_positions.get(f"{trade_id}_partial_taken"):
            self.open_positions[f"{trade_id}_partial_taken"] = True
            return {"Action": "PARTIAL_CLOSE", "Percentage": 50.0, "Reason": "Partial Profit Reached"}

        # 3. Break-Even Adjustments[cite: 2]
        # Move stop loss to entry price once the trade is 30% towards the target
        if progress_pct >= 30.0 and not self.open_positions.get(f"{trade_id}_breakeven_set"):
            self.open_positions[f"{trade_id}_breakeven_set"] = True
            return {"Action": "MODIFY_SL", "New SL": entry_price, "Reason": "Break-Even Adjustment"}

        # 4. Trailing Stops[cite: 2]
        # Once safely in profit, trail the stop manually to lock in gains
        if progress_pct >= 50.0:
            trailing_sl = entry_price + (price_travel * 0.5) # Example: trail by half the distance travelled
            return {"Action": "MODIFY_SL", "New SL": trailing_sl, "Reason": "Trailing Stop Update"}

        return {"Action": "HOLD", "Reason": "Monitoring"}

if __name__ == "__main__":
    # --- Simulate Risk Allocation ---
    allocator = RiskAllocator(account_balance=100000.0)
    
    print("\n--- Risk Allocator Output ---")
    allocation = allocator.calculate_position(confidence=85.0, risk_threat=20.0, atr=2.45)
    for key, value in allocation.items():
        print(f"{key}: {value}")

    # --- Simulate Live Trade Management ---
    manager = TradeManager()
    
    print("\n--- Trade Manager Output ---")
    # Simulate a trade that has moved 80% towards its target
    management_action = manager.manage_trade(
        trade_id="TRD_001",
        current_price=108.0,
        entry_price=100.0,
        initial_sl=96.0,
        target_price=110.0,
        time_in_trade_bars=12
    )
    for key, value in management_action.items():
        print(f"{key}: {value}")