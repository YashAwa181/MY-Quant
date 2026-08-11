import zmq

def start_subscriber(port=5555):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://127.0.0.1:{port}")
    socket.setsockopt_string(zmq.SUBSCRIBE, "TRADE_SIGNAL")

    print(f"--- [Mock C++ Gateway] Listening on tcp://127.0.0.1:{port} ---")

    while True:
        try:
            raw_msg = socket.recv_string()
            payload = raw_msg.replace("TRADE_SIGNAL ", "")
            print(f"[Intercepted Signal] -> {payload}")
        except KeyboardInterrupt:
            print("\nShutting down subscriber.")
            break

if __name__ == "__main__":
    start_subscriber()