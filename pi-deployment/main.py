from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
import json
#import random 
from pymavlink import mavutil # ADDED: import pymavlink to read real MAVLink data

app = FastAPI(title="Battery Monitor", version="1.0.0")

# ── MAVLink connection ──────────────────────────────────────
# ADDED: connect to BlueOS MAVLink router running on the Pi
mav = mavutil.mavlink_connection('udp:localhost:14550')

print("Waiting for MAVLink heartbeat...")
mav.wait_heartbeat()                             # ADDED: blocks until ArduSub responds
print(f"Heartbeat received from system {mav.target_system}")

# ── Real data source ────────────────────────────────────────

def get_battery() -> dict:
    # CHANGED: was random.uniform / random.randint
    msg = mav.recv_match(type='BATTERY_STATUS', blocking=True, timeout=3.0)
    if not msg:
        return {"voltage": 0.0, "remaining": -1, "error": "no data"}
    return {
        "voltage":   round(msg.voltages[0] / 1000, 2),  # mV → V
        "remaining": msg.battery_remaining,
    }


# ── REST endpoint ───────────────────────────────────────────

@app.get("/battery", summary="Current battery snapshot")
async def battery_snapshot():
    return get_battery()

# ── WebSocket stream ────────────────────────────────────────

@app.websocket("/ws/battery")
async def battery_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = get_battery()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1.0)   # 1Hz is fine for battery
    except Exception:
        await websocket.close()

# ── Frontend ────────────────────────────────────────────────

@app.get("/ui", response_class=HTMLResponse)
async def ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Battery Monitor</title>
      <style>
        body { font-family: monospace; padding: 2rem; background: #111; color: #eee; }
        .value { font-size: 3rem; color: #4fc; }
        .label { font-size: 1rem; color: #888; margin-top: 1rem; }
        .error { font-size: 1rem; color: #f44; margin-top: 1rem; }
      </style>
    </head>
    <body>
      <div class="label">Voltage</div>
      <div class="value" id="voltage">--</div>

      <div class="label">Remaining</div>
      <div class="value" id="remaining">--</div>

      <div class="error" id="error"></div>

      <script>
        // CHANGED: localhost → location.host
        // so it works from blueos.local:8000/ui, not just localhost
        const ws = new WebSocket('ws://' + location.host + '/ws/battery')
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          // ADDED: error handling for no MAVLink data
          document.getElementById('voltage').textContent
            = data.error ? '?' : data.voltage + ' V'
          document.getElementById('remaining').textContent
            = data.error ? '?' : data.remaining + ' %'
          document.getElementById('error').textContent
            = data.error ?? ''
        }
      </script>
    </body>
    </html>
    """