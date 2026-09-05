from flask import Flask, request, jsonify
import threading
import time
import random

app = Flask(__name__)

device_state = {
    "speed": 0,
    "fuel_level": 0,
    "switch_status": "off",
    "connected_clients": {}
}

state_lock = threading.Lock()

@app.route('/command', methods=['POST'])
def handle_command():
    global device_state
    try:
        data = request.get_json()
        client_id = data.get('client_id', 'unknown_client')
        command_type = data.get('type')
        value = data.get('value')

        with state_lock:
            if command_type == 'speed':
                if device_state['fuel_level'] >= 5:
                    device_state['speed'] = int(value)
                    device_state['fuel_level'] -= 5
                print(f"[SERVER] {client_id} set motor speed to {device_state['speed']}")

            elif command_type == 'toggle_switch':
                if device_state['switch_status'] == "off":
                    device_state['switch_status'] = "on"
                else:
                    device_state['switch_status'] = "off"

                print(f"[SERVER] {client_id} toggled switch to "
                      f"{device_state['switch_status']}")

            elif command_type == 'fuel_level':
                if device_state['fuel_level'] < 500:
                    device_state['fuel_level'] += 100

                print(f"[SERVER] {client_id} set motor fuel level to {device_state['fuel_level']}")

            else:
                print(f"[SERVER] {client_id} sent unknown command: {command_type}")
                return jsonify({
                    "status": "error",
                    "message": "Unknown command"
                }), 400

            device_state['last_command_time'] = time.time()
            device_state['connected_clients'][client_id] = time.time()

            return jsonify({
                "status": "success",
                "message": f"Command '{command_type}' received."
            })

    except Exception as e:
        print(f"[SERVER] Error handling command: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route('/status', methods=['GET'])
def get_status():
    with state_lock:
        return jsonify(device_state.copy())


def device_simulator():
    global device_state

    while True:
        with state_lock:
            if device_state['speed'] > 0:
                device_state['speed'] = max(
                    0,
                    device_state['speed'] - random.randint(0, 5)
                )

            current_time = time.time()

            inactive_clients = [
                cid
                for cid, ts in device_state['connected_clients'].items()
                if (current_time - ts) > 10
            ]

            for cid in inactive_clients:
                print(f"[SERVER] Client {cid} went inactive.")
                del device_state['connected_clients'][cid]

        time.sleep(1)


simulator_thread = threading.Thread(
    target=device_simulator,
    daemon=True
)
simulator_thread.start()

if __name__ == '__main__':
    print("[SERVER] Starting server on http://0.0.0.0:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)