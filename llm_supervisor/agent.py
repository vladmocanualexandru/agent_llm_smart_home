# agent.py
import os, json, requests
from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://host.docker.internal:11434/v1")
MODEL       = os.getenv("MODEL", "llama3.1:8b-instruct-q4_0")
SIM_BASE    = os.getenv("SIM_BASE", "http://localhost:5555")  # your simulator

app = FastAPI(title="Smart Home Agent")

client = OpenAI(base_url=OLLAMA_BASE, api_key="ollama")  # key ignored by Ollama


# ---- Simulator tool bindings ----
def sim_get_status() -> Dict[str, Any]:
    r = requests.get(f"{SIM_BASE}/devices", timeout=10)
    r.raise_for_status()
    return r.json()

def sim_set_power(device_id: str, power: str) -> Dict[str, Any]:
    action = "turn-on" if power == "on" else "turn-off"
    r = requests.get(f"{SIM_BASE}/device/{device_id}/{action}", timeout=10)
    r.raise_for_status()
    return r.json()

TOOLS_SCHEMA = [
  {
    "type":"function",
    "function":{
      "name":"get_status",
      "description":"Read current sensors and device states.",
      "parameters":{"type":"object","properties":{},"required":[]}
    }
  },
  {
    "type":"function",
    "function":{
      "name":"set_device_power",
      "description":"Turn a device on or off.",
      "parameters":{
        "type":"object",
        "properties":{
          "device_id":{"type":"string"},
          "power":{"type":"string","enum":["on","off"]}
        },
        "required":["device_id","power"]
      }
    }
  },
]

TOOL_IMPL = {
    "get_status": lambda **kwargs: sim_get_status(),
    "set_device_power": sim_set_power,
}

SYSTEM_PROMPT = """You are a home-automation assistant controlling a simulator via tools.
Policy:
- Be conservative and explain actions.
- Prefer minimal changes to reach comfort.
- Typical comfort: temp 21–23°C, humidity 40–55%, light 75-120lux.
- After acting, re-check status when helpful and report results.
- Never spam actions; max 5 tool calls per request.
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
    print(body)

    messages = [
        {"role":"system","content": SYSTEM_PROMPT},
        {"role":"user","content": body.user}
    ]
    actions_log: List[Dict[str, Any]] = []

    for _ in range(5):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS_SCHEMA, tool_choice="auto"
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
                    "role":"tool","tool_call_id":tc.id,
                    "content": json.dumps({"ok": True, "dry_run": True, "tool": name, "args": args})
                })
                continue

            try:
                result = TOOL_IMPL[name](**args)
                actions_log.append({"tool": name, "args": args, "result": result})
                messages.append({"role":"tool","tool_call_id":tc.id,"content": json.dumps(result)})
            except Exception as e:
                err = {"error": str(e)}
                actions_log.append({"tool": name, "args": args, "result": err})
                messages.append({"role":"tool","tool_call_id":tc.id,"content": json.dumps(err)})

        # ask model to summarize after tool feedback
        messages.append({"role":"system","content":"Summarize what you did succinctly; include rationale."})

    # graceful fallback
    status = sim_get_status()
    return ChatOut(
        reply="I reached the max step limit. Here is the current status and what I attempted.",
        actions=actions_log, final_status=status
    )

@app.get("/healthz")
def healthz():
    return {"ok": True}
