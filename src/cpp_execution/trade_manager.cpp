#include <iostream>
#include <string>
#include <unordered_map>
#include <cmath>

// Struct to track the memory of each active trade
struct TradeState {
    bool partial_taken = false;
    bool breakeven_set = false;
};

class TradeManager {
private:
    // Internal state tracker for open positions
    std::unordered_map<std::string, TradeState> open_positions;

public:
    TradeManager() {
        std::cout << "[TradeManager] Initialised and ready for live execution.\n";
    }

    /**
     * Dynamically adjusts open orders based on price action[cite: 2].
     */
    void manage_trade(const std::string& trade_id, double current_price, double entry_price, 
                      double initial_sl, double target_price, int time_in_trade_bars) {
        
        // Calculate current floating progress
        double price_travel = std::abs(current_price - entry_price);
        double distance_to_target = std::abs(target_price - entry_price);
        
        double progress_pct = 0.0;
        if (distance_to_target > 0) {
            progress_pct = (price_travel / distance_to_target) * 100.0;
        }

        // 1. Time-Based Exits[cite: 2]
        // If the trade has stagnated for too long, close it to free up capital
        if (time_in_trade_bars > 48) {
            std::cout << "[TRD-" << trade_id << "] ACTION: CLOSE_POSITION | Reason: Time-Based Exit\n";
            // Clean up the map
            open_positions.erase(trade_id);
            return;
        }

        // 2. Partial Profit-Taking[cite: 2]
        // Secure 50% of the position if price reaches 75% of the target
        if (progress_pct >= 75.0 && !open_positions[trade_id].partial_taken) {
            open_positions[trade_id].partial_taken = true;
            std::cout << "[TRD-" << trade_id << "] ACTION: PARTIAL_CLOSE | Percentage: 50.0% | Reason: Partial Profit Reached\n";
        }

        // 3. Break-Even Adjustments[cite: 2]
        // Move stop loss to entry price once the trade is 30% towards the target
        if (progress_pct >= 30.0 && !open_positions[trade_id].breakeven_set) {
            open_positions[trade_id].breakeven_set = true;
            std::cout << "[TRD-" << trade_id << "] ACTION: MODIFY_SL | New SL: " << entry_price << " | Reason: Break-Even Adjustment\n";
        }

        // 4. Trailing Stops[cite: 2]
        // Once safely in profit, trail the stop manually to lock in gains
        if (progress_pct >= 50.0) {
            // Determine direction (1 for Long, -1 for Short)
            int direction = (target_price > entry_price) ? 1 : -1;
            
            // Trail by half the distance travelled
            double trailing_sl = entry_price + (direction * price_travel * 0.5); 
            
            std::cout << "[TRD-" << trade_id << "] ACTION: MODIFY_SL | New SL: " << trailing_sl << " | Reason: Trailing Stop Update\n";
        }
    }
};

// --- Quick testing block ---
int main() {
    TradeManager manager;
    
    std::cout << "\n--- Simulating Live Market Updates ---\n";
    
    // Simulating a Long trade that has progressed 80% towards its target
    manager.manage_trade(
        "EURUSD_001", // Trade ID
        1.1080,       // Current Price
        1.1000,       // Entry Price
        1.0960,       // Initial SL
        1.1100,       // Target Price
        12            // Time in trade (bars)
    );

    return 0;
}