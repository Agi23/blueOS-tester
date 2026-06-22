from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
import json
import random   # remove this when using real MAVLink

app = FastAPI(title="Battery Monitor", version="1.0.0")

# ── Simulated data source (replace with pymavlink call) ────

def get_battery() -> dict:
    """
    In production: read from MAVLink BATTERY_STATUS message.
    In simulation: return realistic fake values.
    """
    return {
        "voltage":   round(random.uniform(14.0, 16.8), 2),
        "remaining": random.randint(60, 100),
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

# ── Minimal frontend served directly from Python ───────────

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
      </style>
    </head>
    <body>
      <div class="label">Voltage</div>
      <div class="value" id="voltage">--</div>

      <div class="label">Remaining</div>
      <div class="value" id="remaining">--</div>

      <script>
        const ws = new WebSocket('ws://localhost:8000/ws/battery')
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data)
          document.getElementById('voltage').textContent   = data.voltage + ' V'
          document.getElementById('remaining').textContent = data.remaining + ' %'
        }
      </script>
    </body>
    </html>
    """