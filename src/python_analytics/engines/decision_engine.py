import pandas as pd

class DecisionEngine:
    def __init__(self, confidence_threshold: float = 40.0, confirmation_bars: int = 3):
        """
        Initializes the Decision Engine to validate MIE signals before execution.
        
        :param confidence_threshold: Minimum score required to exit a Neutral State.
        :param confirmation_bars: Number of consecutive bars a state must hold 
                                  to pass the confirmation timer.
        """
        self.confidence_threshold = confidence_threshold
        self.confirmation_bars = confirmation_bars
        
        # Internal memory for hysteresis and timers
        self.state_history = []
        self.current_validated_state = "Neutral"

    def _apply_confirmation_timer(self, raw_state: str) -> str:
        """
        Requires a new market regime to persist for N consecutive bars 
        before officially validating the transition (Confirmation Timer)[cite: 2].
        """
        self.state_history.append(raw_state)
        
        # Keep only the memory required for the timer
        if len(self.state_history) > self.confirmation_bars:
            self.state_history.pop(0)
            
        # If the history isn't full yet, maintain the current validated state
        if len(self.state_history) < self.confirmation_bars:
            return self.current_validated_state
            
        # If every bar in the recent memory matches the raw state, the timer is complete
        if all(state == raw_state for state in self.state_history):
            self.current_validated_state = raw_state
            
        return self.current_validated_state

    def _apply_hysteresis(self, validated_state: str, confidence: float) -> str:
        """
        Applies hysteresis to prevent flickering between active and neutral states[cite: 2].
        If the system is already in a trade, it requires a lower confidence 
        to stay in the trade than it required to enter it.
        """
        # Hysteresis band: Entry requires standard threshold, exit triggers at threshold - 15
        exit_threshold = self.confidence_threshold - 15.0
        
        if self.current_validated_state != "Neutral":
            # We are currently active. Only drop to Neutral if confidence collapses severely.
            if confidence < exit_threshold:
                return "Neutral"
            return validated_state
        else:
            # We are currently Neutral. Require full confidence threshold to activate.
            if confidence >= self.confidence_threshold:
                return validated_state
            return "Neutral"

    def evaluate_signal(self, raw_phase: str, confidence_score: float) -> dict:
        """
        Evaluates the raw data and outputs a strict execution signal.
        """
        # 1. Apply the Confirmation Timer[cite: 2]
        timer_state = self._apply_confirmation_timer(raw_phase)
        
        # 2. Apply Confidence Threshold and Hysteresis[cite: 2]
        final_decision_state = self._apply_hysteresis(timer_state, confidence_score)
        
        # 3. Determine Neutral State condition[cite: 2]
        is_neutral = final_decision_state == "Neutral"
        
        return {
            "Raw MIE Phase": raw_phase,
            "Confidence Input": confidence_score,
            "Timer Validated State": timer_state,
            "Final Execution State": final_decision_state,
            "Trading Permitted": not is_neutral
        }

if __name__ == "__main__":
    # Simulate a noisy market transition
    engine = DecisionEngine(confidence_threshold=50.0, confirmation_bars=3)
    
    print("\n--- Decision Engine Hysteresis Test ---")
    
    # Tick 1: Market enters "Trend" but confidence is low
    print(engine.evaluate_signal(raw_phase="Trend", confidence_score=45.0))
    
    # Tick 2: Trend holds, confidence spikes
    print(engine.evaluate_signal(raw_phase="Trend", confidence_score=85.0))
    
    # Tick 3: Trend holds for the 3rd bar (Confirmation Timer triggers), confidence remains high
    print(engine.evaluate_signal(raw_phase="Trend", confidence_score=88.0))
    
    # Tick 4: Market gets noisy, confidence drops to 40. 
    # (Hysteresis keeps it in "Trend" because 40 > the exit threshold of 35)
    print(engine.evaluate_signal(raw_phase="Trend", confidence_score=40.0))