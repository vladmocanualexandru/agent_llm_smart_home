# agent.py
import os, json, requests
from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434/v1")
MODEL       = os.getenv("MODEL", "llama3.1:8b-instruct-q4_0")
SIM_BASE    = os.getenv("SIM_BASE", "http://localhost:5555")  # your simulator

client = OpenAI(base_url=OLLAMA_BASE, api_key="ollama")  # key ignored by Ollama
app = FastAPI(title="Smart Home Agent")

WEB_ROOT = os.path.join(os.path.dirname(__file__), "static")
app.mount("/assets", StaticFiles(directory=WEB_ROOT), name="assets")    

@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_ROOT, "index.html"))

# ---- Simulator bindings ----
def sim_get_status() -> Dict[str, Any]:
    r = requests.get(f"{SIM_BASE}/devices", timeout=10)
    r.raise_for_status()
    return r.json()

def sim_list_devices() -> Dict[str, Any]:
    r = requests.get(f"{SIM_BASE}/devices", timeout=10)
    r.raise_for_status()
    return r.json()

def sim_set_power(device_id: str, power: str) -> Dict[str, Any]:
    action = "turn-on" if power == "on" else "turn-off"
    r = requests.get(f"{SIM_BASE}/device/{device_id}/{action}", timeout=10)
    r.raise_for_status()
    return r.json()

# Build tool schemas dynamically based on /devices
def build_tools_schema() -> List[Dict[str, Any]]:
    devices = sim_list_devices()  # { "<device_id>": {...}, ... }
    device_ids = sorted(devices.keys())

    # if you have tons of devices, avoid huge enums
    enum_ids = ['heater_1','heater_2','room_light','reading_light','party_light_left','humidifier', 'dehumidifier', 'curtains_left', 'curtains_right','air_conditioner_couch','air_conditioner_entry']
    # enum_ids = device_ids if len(device_ids) <= 100 else None

    def device_id_schema():
        # Prefer enum with exact IDs; fall back to free string if too many
        return {"type": "string", **({"enum": enum_ids} if enum_ids else {})}

    return [
        {
            "type": "function",
            "function": {
                "name": "list_devices",
                "description": "Return all devices and their IDs from the simulator.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_status",
                "description": "Read current sensors and device states.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "set_device_power",
                "description": "Turn a device on or off. Use a valid device_id from {'heater_1','heater_2','room_light','reading_light','party_light_left','humidifier', 'dehumidifier', 'curtains_left', 'curtains_right','air_conditioner_couch','air_conditioner_entry'}. Use only one call per device, do not send multiple device ids per call.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "device_id": device_id_schema(),
                        "power": {"type": "string", "enum": ["on", "off"]},
                    },
                    "required": ["device_id", "power"],
                },
            },
        }
    ]

TOOL_IMPL = {
    "list_devices": lambda **_: sim_list_devices(),
    "get_status":   lambda **_: sim_get_status(),
    "set_device_power": sim_set_power,
}

# SYSTEM_PROMPT = """You are a home-automation assistant controlling a simulator via tools.
# Policy:
# - Be conservative and explain actions.
# - Prefer minimal changes to reach comfort.
# - Typical comfort: temp 21–23°C, humidity 40–55%, light between 75 and 125lux.
# - When uncertain which device to use, call list_devices and pick a matching ID.
# - After acting, re-check status when helpful and report results.
# - Never spam actions; max 5 tool calls per request.
# """

SYSTEM_PROMPT = """You are a home-automation assistant controlling a simulator via tools.
Policy:
- Be conservative and explain actions.
- Feel free to use all available devices (multiple heaters, ACs, lights, curtains)
- Typical comfort: temp 21–23°C, humidity 40–55%, light between 75 and 125lux.
- When uncertain which device to use, call list_devices and pick a matching ID.
- After acting, re-check status when helpful and report results.
- Do not make a single call for multiple devices
- Never spam actions; max 10 tool calls per request.
"""

class ChatIn(BaseModel):
    user: str
    dry_run: Optional[bool] = False

class ChatOut(BaseModel):
    reply: str
    actions: List[Dict[str, Any]] = []
    final_status: Optional[Dict[str, Any]] = None

@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    # refresh tools from live device list every turn
    tools_schema = build_tools_schema()


    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": body.user},
    ]
    actions_log: List[Dict[str, Any]] = []

    for _ in range(10):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools_schema, tool_choice="auto"
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return ChatOut(reply=msg.content or "(no content)", actions=actions_log)

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")

            if body.dry_run:
                actions_log.append({"tool": name, "args": args, "result": "(dry-run)"})
                messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps({"ok": True, "dry_run": True, "tool": name, "args": args})
                })
                continue

            try:
                result = TOOL_IMPL[name](**args)
            except Exception as e:
                result = {"error": str(e)}

            actions_log.append({"tool": name, "args": args, "result": result})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

        messages.append({"role": "system", "content": "Summarize what you did succinctly; include rationale."})

    status = None
    try:
        status = sim_get_status()
    except Exception:
        pass
    return ChatOut(
        reply="I reached the max step limit. Here is what I attempted.",
        actions=actions_log, final_status=status
    )

@app.get("/healthz")
def healthz():
    return {"ok": True}
