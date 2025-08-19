from webapp import flaskApp
from flask import jsonify, request, render_template
import threading
import time
import random

CLIMATE_CHANGE_STEP_THRESHOLD=30

# In-memory store for devices
devices = {
    "heater_1": {
        "type": "control", 
        "activated": False,
        "effect": {
            "temperature_sensor":{
                "value": 0.5,
                "instant": False
            }
        },
        "ui": {
            "x": 3.5, "y": 61,
            "icon": "heater"
        }
    },
    "heater_2": {
        "type": "control", 
        "activated": False,
        "effect": {
            "temperature_sensor":{
                "value": 0.5,
                "instant": False
            }
        },
        "ui": {
            "x": 3.5, "y": 81,
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
    "air_conditioner_couch": {
        "type": "control", 
        "activated": False,
        "effect": {
            "temperature_sensor":{
                "value": -0.3,
                "instant": False
            }
        },
        "ui": {
            "x":44.4, "y": 0.5,
            "icon": "ac"
        }
    },
    "air_conditioner_entry": {
        "type": "control", 
        "activated": False,
        "effect": {
            "temperature_sensor":{
                "value": -0.3,
                "instant": False
            }
        },
        "ui": {
            "x": 95, "y": 76,
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

steps_counter = 0
climate_temp_variation = 0
climate_light_variation = 100
climate_humidity_variation = 0

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

@flaskApp.route("/device/<device_id>/turn-on", methods=["GET"])
def turn_on_device(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

    devices[device_id]["activated"] = True
    return jsonify({"message": "Device turned on", "device": devices[device_id]})

@flaskApp.route("/device/<device_id>/turn-off", methods=["GET"])
def turn_off_device(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

    devices[device_id]["activated"] = False
    return jsonify({"message": "Device turned off", "device": devices[device_id]})

@flaskApp.route("/device/<device_id>/toggle", methods=["GET"])
def toggle_device(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

    current_state = devices[device_id].get("activated")
    if current_state is None:
        return jsonify({"error": "Device cannot be toggled"}), 400

    devices[device_id]["activated"] = not current_state
    return jsonify({"message": "Device toggled", "device": devices[device_id]})

def update_sensors():
    global climate_temp_variation, climate_light_variation, climate_humidity_variation, steps_counter

    while True:
        # Temperature sensor update
        temp = devices["temperature_sensor"]["data"]["value"] + climate_temp_variation
        for device_id, device in devices.items():
            if device.get("activated") and "temperature_sensor" in device.get("effect", {}):
                effect = device["effect"]["temperature_sensor"]
                temp += effect["value"]
        devices["temperature_sensor"]["data"]["value"] = round(temp, 2)

        # Humidity sensor update
        humidity = devices["humidity_sensor"]["data"]["value"] + climate_humidity_variation
        for device_id, device in devices.items():
            if device.get("activated") and "humidity_sensor" in device.get("effect", {}):
                effect = device["effect"]["humidity_sensor"]
                humidity += effect["value"]
        devices["humidity_sensor"]["data"]["value"] = round(humidity, 2)

        light = climate_light_variation
        for device_id, device in devices.items():
            if device.get("activated") and "light_sensor" in device.get("effect", {}):
                effect = device["effect"]["light_sensor"]
                light += effect["value"]
        devices["light_sensor"]["data"]["value"] = max(0,round(light, 2))

        time.sleep(1)

        steps_counter += 1

        if steps_counter % CLIMATE_CHANGE_STEP_THRESHOLD == 0:
            steps_counter = 0

            climate_temp_variation = random.uniform(-0.2, 0.2)
            climate_light_variation = random.uniform(0, 100)
            climate_humidity_variation = random.uniform(-0.2, 0.2)


sensor_thread = threading.Thread(target=update_sensors, daemon=True)
sensor_thread.start()