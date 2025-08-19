from webapp import flaskApp
from flask import jsonify, request, render_template

# In-memory store for devices
devices = {
    "heater": {
        "type": "control", 
        "activated": True,
        "effect": {
            "temperature_sensor":{
                "value": 0.1,
                "instant": False
            }
        },
        "ui": {
            "x": 3.5, "y": 71,
            "icon": "heater"
        }
    },
    "room_light": {
        "type": "control", 
        "activated": False,
        "effect": {
            "light_sensor":{
                "value": 30,
                "instant": True
            }
        },
        "ui": {
            "x": 46.4, "y": 48.7,
            "icon": "light"
        }
    },
    "reading_light": {
        "type": "control", 
        "activated": False,
        "effect": {
            "light_sensor":{
                "value": 20,
                "instant": True
            }
        },
        "ui": {
            "x": 65.4, "y": 12.7,
            "icon": "light"
        }
    },
    "party_light_left": {
        "type": "control", 
        "activated": False,
        "effect": {
            "light_sensor":{
                "value": 30,
                "instant": True
            }
        },
        "ui": {
            "x": 14, "y": 82,
            "icon": "light"
        }
    },
    "humidifier": {
        "type": "control", 
        "activated": False,
        "effect": {
            "humidity_sensor":{
                "value": 0.2,
                "instant": False
            }
        },
        "ui": {
            "x": 38, "y": 35.2,
            "icon": "humidifier"
        }
    },
    "dehumidifier": {
        "type": "control", 
        "activated": False,
        "effect": {
            "humidity_sensor":{
                "value": -0.1,
                "instant": False
            }
        },
        "ui": {
            "x": 51.7, "y": 35.2,
            "icon": "dehumidifier"
        }
    },
    "curtains_left": {
        "type": "control", 
        "activated": False,
        "effect": {
            "light_sensor":{
                "value": -40,
                "instant": True
            }
        },
        "ui": {
            "x": 2, "y": 25,
            "icon": "curtains"
        }
    },
    "curtains_right": {
        "type": "control", 
        "activated": False,
        "effect": {
            "light_sensor":{
                "value": -40,
                "instant": True
            }
        },
        "ui": {
            "x": 93, "y": 34,
            "icon": "curtains"
        }
    },
    "air_conditioner": {
        "type": "control", 
        "activated": True,
        "effect": {
            "temperature_sensor":{
                "value": -0.2,
                "instant": False
            }
        },
        "ui": {
            "x":44.4, "y": 0.5,
            "icon": "ac"
        }
    },
    "tv": {
        "type": "control", 
        "activated": False,
        "effect": {},
        "ui": {
            "x": 46, "y": 89.4,
            "icon": "tv"
        }
    },
    "massage_seat": {
        "type": "control",
        "activated": False,
        "effect": {},
        "ui": {
            "x":68.6, "y": 29.7,
            "icon": "massage_seat"
        }
    },
    "temperature_sensor": {
        "type": "sensor", 
        "data": {
            "value": 30, "unit": "C"
        }
    },
    "humidity_sensor": {
        "type": "sensor", 
        "data": {
            "value": 50, "unit": "%"
        }
    },
    "light_sensor": {
        "type": "sensor", 
        "data": {
            "value": 100, "unit": "lux"
        }
    }
}

@flaskApp.route("/", methods=["GET"])
def get_homepage():
    return render_template("home.html")

@flaskApp.route("/devices", methods=["GET"])
def get_devices():
    return jsonify(devices)

@flaskApp.route("/device/<device_id>", methods=["GET"])
def get_device(device_id):
    device = devices.get(device_id)
    return jsonify(device) if device else (jsonify({"error": "Device not found"}), 404)

@flaskApp.route("/device/<device_id>/set", methods=["POST"])
def set_device(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

    update_data = request.json
    devices[device_id].update(update_data)
    return jsonify({"message": "Device updated", "device": devices[device_id]})
