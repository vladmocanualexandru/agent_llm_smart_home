from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory store for devices
devices = {
    "living_room_light": {"type": "light", "state": "off", "brightness": 100, "color": "white"},
    "bedroom_fan": {"type": "fan", "state": "off", "speed": "medium"},
    "thermostat": {"type": "thermostat", "temperature": 22},
}

@app.route("/devices", methods=["GET"])
def get_devices():
    return jsonify(devices)

@app.route("/device/<device_id>", methods=["GET"])
def get_device(device_id):
    device = devices.get(device_id)
    return jsonify(device) if device else (jsonify({"error": "Device not found"}), 404)

@app.route("/device/<device_id>/set", methods=["POST"])
def set_device(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

    update_data = request.json
    devices[device_id].update(update_data)
    return jsonify({"message": "Device updated", "device": devices[device_id]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
