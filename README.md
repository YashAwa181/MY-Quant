# MY-Quant: Hybrid Quantitative Trading & Analytics Platform

`MY-Quant` is a high-performance, modular algorithmic trading and quantitative analytics engine. It combines a **Python-based analytical pipeline** for feature engineering, regime/market state analysis, and decision scoring with a **C++ low-latency execution gateway** communicated via ZeroMQ IPC messaging.

---

## 🏗 System Architecture

```
                    ┌──────────────────────────────────────────┐
                    │            Data Sources / Inputs         │
                    └────────────────────┬─────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           PYTHON ANALYTICS ENGINE                            │
│                                                                              │
│  ┌──────────────────────┐    ┌────────────────────────────────────────────┐  │
│  │    Data Pipeline     │───►│                 Analysers                  │  │
│  │ • Data Loader        │    │ • Trend, Volatility, Momentum              │  │
│  │ • Feature Calculator │    │ • Liquidity, Structure, Behaviour, Risk    │  │
│  └──────────────────────┘    └─────────────────────┬──────────────────────┘  │
│                                                    │                         │
│                                                    ▼                         │
│  ┌──────────────────────┐    ┌────────────────────────────────────────────┐  │
│  │    Market Memory     │◄───│                  Engines                   │  │
│  │ • SQLite (db)        │    │ • Strategy, Decision, Confidence           │  │
│  │ • Memory Listener    │    │ • Transition Detector, MIE Scorer           │  │
│  └──────────────────────┘    └─────────────────────┬──────────────────────┘  │
└────────────────────────────────────────────────────┼─────────────────────────┘
                                                     │ ZeroMQ IPC (Publisher)
                                                     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                             C++ EXECUTION GATEWAY                            │
│                                                                              │
│   ┌───────────────────────────┐         ┌─────────────────────────────────┐  │
│   │    ZeroMQ Subscriber      │────────►│          Trade Manager          │  │
│   └───────────────────────────┘         └────────────────┬────────────────┘  │
│                                                          │                   │
│                                                          ▼                   │
│                                         ┌─────────────────────────────────┐  │
│                                         │         Risk Allocator          │  │
│                                         └─────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
MY-Quant/
├── data/
│   └── market_memory.db          # SQLite database for storing market states & memory
├── src/
│   ├── cpp_execution/            # C++ Low-Latency Execution Core
│   │   ├── build/
│   │   │   └── CMakeLists.txt    # Build configuration for CMake
│   │   ├── execution_gateway.cpp # Main entry point for C++ execution gateway
│   │   ├── risk_allocator.cpp    # Risk management & sizing engine (C++)
│   │   ├── trade_manager.cpp     # Trade lifecycle & order routing
│   │   ├── test_subscriber.py    # Python subscriber for testing ZeroMQ IPC
│   │   ├── zmq.h / zmq.hpp       # ZeroMQ C++ headers
│   │   └── execution_gateway.exe # Compiled executable
│   │
│   └── python_analytics/         # Python Analytics & Signal Pipeline
│       ├── main_publisher.py     # Central publisher broadcasting signals via ZeroMQ
│       ├── data_pipeline/
│       │   ├── data_loader.py    # Historical & real-time market data ingestion
│       │   └── feature_calculator.py # Technical indicators & feature engineering
│       ├── analysers/            # Domain-specific quantitative analysers
│       │   ├── trend_analyser.py
│       │   ├── volatility_analyser.py
│       │   ├── momentum_analyser.py
│       │   ├── liquidity_analyser.py
│       │   ├── structure_analyser.py
│       │   ├── behaviour_analyser.py
│       │   └── risk_intelligence.py
│       ├── engines/              # Signal generation & decision engines
│       │   ├── strategy_engine.py
│       │   ├── decision_engine.py
│       │   ├── confidence_engine.py
│       │   ├── transition_detector.py
│       │   ├── mie_scorer.py
│       │   └── risk_allocator.py
│       └── memory/               # Market state persistence & historical lookup
│           ├── market_memory.py  # SQLite Interface for market memory
│           └── memory_listener.py# Subscriber to persist state transitions
│
└── tests/
    └── backtest_simulator.py     # Event-driven backtesting & simulation engine
```

---

## 🔑 Key Components

### 1. Python Analytics Engine
* **Data Pipeline (`data_pipeline/`)**: Ingests price/volume data and computes microstructural and technical features.
* **Analysers (`analysers/`)**: Modular components evaluating market factors including momentum, volatility, market structure, liquidity, and participant behaviour.
* **Core Engines (`engines/`)**: Combines analytical outputs using multi-factor confidence scoring (`confidence_engine.py`, `mie_scorer.py`) and regime transition detection (`transition_detector.py`) to output actionable trading signals.
* **Market Memory (`memory/`)**: Maintains an active SQLite database (`market_memory.db`) storing historical market states, regimes, and feature histories to inform real-time decision-making.

### 2. C++ Low-Latency Execution Gateway (`cpp_execution/`)
* **ZeroMQ IPC Interface**: Listens to published signals from Python analytics with minimal serialization overhead.
* **Trade Manager (`trade_manager.cpp`)**: Manages position lifecycle, active orders, and order execution logic.
* **Risk Allocator (`risk_allocator.cpp`)**: Applies strict pre-trade risk controls, dynamic position sizing, and leverage constraints before sending orders.

---

## 🚀 Getting Started

### Prerequisites

* **Python**: `3.12+`
* **C++ Compiler**: GCC / Clang / MSVC supporting C++17 or higher
* **Build System**: CMake `3.10+`
* **Dependencies**:
  * ZeroMQ (`libzmq` and C++ bindings `cppzmq`)
  * Python packages: `numpy`, `pandas`, `pyzmq`, `sqlite3`

---

## 🛠 Building & Running

### 1. Build the C++ Execution Gateway

```bash
cd src/cpp_execution
mkdir -p build && cd build
cmake ..
cmake --build .
```

### 2. Run the Backtest Simulator

To validate strategies historically:

```bash
python -m tests.backtest_simulator
```

### 3. Run in Live / Simulated IPC Mode

**Step A:** Launch the C++ Execution Gateway (Subscriber)

```bash
./src/cpp_execution/build/execution_gateway
```

**Step B:** Launch the Python Analytics Publisher

```bash
python -m src.python_analytics.main_publisher
```

---

## 🧪 Testing ZeroMQ Communications

You can verify IPC socket messaging between components using the provided python test subscriber:

```bash
python src/cpp_execution/test_subscriber.py
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
