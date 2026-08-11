// #include <zmq.hpp>
// #include <iostream>
// #include <string>
// #include <nlohmann/json.hpp> // Standard C++ JSON library

// using json = nlohmann::json;

// class ExecutionGateway {
// private:
//     zmq::context_t context;
//     zmq::socket_t subscriber;

// public:
//     ExecutionGateway(const std::string& address) 
//         : context(1), subscriber(context, ZMQ_SUB) {
        
//         subscriber.connect(address);
//         // Subscribe only to messages starting with "TRADE_SIGNAL"
//         subscriber.set(zmq::sockopt::subscribe, "TRADE_SIGNAL");
//         std::cout << "C++ Execution Gateway listening on " << address << "...\n";
//     }

//     void listen_and_execute() {
//         while (true) {
//             zmq::message_t update;
            
//             // Block until a message is received from Python
//             auto res = subscriber.recv(update, zmq::recv_flags::none);
//             if (res) {
//                 std::string msg = update.to_string();
                
//                 // Strip the "TRADE_SIGNAL " prefix to isolate the JSON
//                 std::string json_str = msg.substr(13);
                
//                 try {
//                     // Parse the JSON payload
//                     json payload = json::parse(json_str);
                    
//                     // Route to the Risk Allocator and Trade Manager
//                     std::cout << "\n[C++] Signal Intercepted: " << payload["Action"] << " " << payload["Asset"] << "\n";
//                     std::cout << "[C++] Initiating dynamic lot sizing and ATR stops...\n";
                    
//                     // TODO: Pass 'payload' into C++ RiskAllocator class
                    
//                 } catch (json::parse_error& e) {
//                     std::cerr << "JSON Parsing Error: " << e.what() << '\n';
//                 }
//             }
//         }
//     }
// };

// int main() {
//     ExecutionGateway gateway("tcp://127.0.0.1:5555");
//     gateway.listen_and_execute();
//     return 0;
// }
 //---------------------------------------------------------------
// #include <iostream>
// #include <string>
// #include <chrono>
// #include <iomanip>
// #include "zmq.hpp"

// // Single-header JSON parsing (or basic string extraction if nlohmann is unlinked)
// class SimpleExecutionGateway {
// private:
//     zmq::context_t context;
//     zmq::socket_t subscriber;

// public:
//     SimpleExecutionGateway(const std::string& address) 
//         : context(1), subscriber(context, ZMQ_SUB) {
        
//         subscriber.connect(address);
//         // Subscribe to the TRADE_SIGNAL channel
//         subscriber.set(zmq::sockopt::subscribe, "TRADE_SIGNAL");
        
//         std::cout << "=================================================\n";
//         std::cout << "   [C++ Execution Gateway] Online & Listening    \n";
//         std::cout << "   Target Socket: " << address << "\n";
//         std::cout << "=================================================\n\n";
//     }

//     void start_listen_loop() {
//         while (true) {
//             zmq::message_t message;
            
//             // Blocking wait for signal from Python Core
//             auto result = subscriber.recv(message, zmq::recv_flags::none);
            
//             if (result) {
//                 std::string raw_msg = message.to_string();
                
//                 // Strip channel header "TRADE_SIGNAL "
//                 std::string payload = raw_msg.substr(13);
                
//                 // Get local microsecond timestamp for latency tracking
//                 auto now = std::chrono::system_clock::now();
//                 auto now_c = std::chrono::system_clock::to_time_t(now);
                
//                 std::cout << "[" << std::put_time(std::localtime(&now_c), "%H:%M:%S") << "] "
//                           << "Signal Intercepted -> " << payload << "\n";
                          
//                 // Fast-path execution trigger
//                 process_execution_rules(payload);
//             }
//         }
//     }

// private:
//     void process_execution_rules(const std::string& json_payload) {
//         // High-speed risk check & order routing logic
//         if (json_payload.find("\"action\": \"BUY\"") != std::string::npos) {
//             std::cout << "   >>> [C++ RISK OK] Firing LONG Market Order <<<\n\n";
//         } 
//         else if (json_payload.find("\"action\": \"SELL\"") != std::string::npos) {
//             std::cout << "   >>> [C++ RISK OK] Firing SHORT Market Order <<<\n\n";
//         } 
//         else {
//             std::cout << "   --- [C++ HOLD] State Neutral. No Order Fired. ---\n\n";
//         }
//     }
// };

// int main() {
//     try {
//         SimpleExecutionGateway gateway("tcp://127.0.0.1:5555");
//         gateway.start_listen_loop();
//     } 
//     catch (const std::exception& e) {
//         std::cerr << "[C++ Error] Exception caught: " << e.what() << std::endl;
//         return 1;
//     }
//     return 0;
// }

// ---------------------------------------------------------

#include <iostream>
#include <string>
#include <chrono>
#include <iomanip>
#include "zmq.hpp"

class ExecutionGateway {
private:
    zmq::context_t context;
    zmq::socket_t subscriber; // Inbound signals from Python (Port 5555)
    zmq::socket_t publisher;  // Outbound trade logs to Python (Port 5556)

public:
    ExecutionGateway(const std::string& sub_addr, const std::string& pub_addr) 
        : context(1), 
          subscriber(context, ZMQ_SUB),
          publisher(context, ZMQ_PUB) {
        
        // Connect Inbound
        subscriber.connect(sub_addr);
        subscriber.set(zmq::sockopt::subscribe, "TRADE_SIGNAL");

        // Bind Outbound
        publisher.bind(pub_addr);
        
        std::cout << "=================================================\n";
        std::cout << "   [C++ Execution Gateway] Online & Connected    \n";
        std::cout << "   Listening on: " << sub_addr << "\n";
        std::cout << "   Broadcasting logs on: " << pub_addr << "\n";
        std::cout << "=================================================\n\n";
    }

    void start_listen_loop() {
        while (true) {
            zmq::message_t message;
            auto result = subscriber.recv(message, zmq::recv_flags::none);
            
            if (result) {
                std::string raw_msg = message.to_string();
                std::string payload = raw_msg.substr(13); // Strip "TRADE_SIGNAL "
                
                std::cout << "[Signal Received] -> " << payload << "\n";
                
                // Process order execution and generate trade outcome
                process_and_log_trade(payload);
            }
        }
    }

private:
    void process_and_log_trade(const std::string& signal_payload) {
        // Simulate order execution and PnL calculation
        if (signal_payload.find("\"action\": \"BUY\"") != std::string::npos ||
            signal_payload.find("\"action\": \"SELL\"") != std::string::npos) {
            
            std::cout << "   >>> [C++ EXECUTION] Order Executed. Monitoring position... <<<\n";

            // Construct JSON execution log payload
            std::string log_json = "{\"status\": \"CLOSED\", \"pnl\": 142.50, \"duration_bars\": 14, \"outcome\": \"Take Profit Hit\"}";
            
            // Broadcast back to Python on Port 5556
            std::string log_msg = "TRADE_LOG " + log_json;
            zmq::message_t log_zmq(log_msg.size());
            memcpy(log_zmq.data(), log_msg.c_str(), log_msg.size());
            publisher.send(log_zmq, zmq::send_flags::none);

            std::cout << "   >>> [C++ FEEDBACK] Episode Log sent to Market Memory <<<\n\n";
        }
    }
};

int main() {
    try {
        ExecutionGateway gateway("tcp://127.0.0.1:5555", "tcp://127.0.0.1:5556");
        gateway.start_listen_loop();
    } 
    catch (const std::exception& e) {
        std::cerr << "[C++ Exception] " << e.what() << std::endl;
        return 1;
    }
    return 0;
}