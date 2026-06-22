# local-dev

Runs the battery monitor on your laptop with simulated MAVLink data. No hardware, no Docker required to get started.

Use this to understand the architecture and iterate on code quickly before touching the Pi.

---

## What It Does

- Serves a REST endpoint at `/battery` returning fake voltage and remaining percentage
- Streams live updates via WebSocket at `/ws/battery` at 1Hz
- Serves a browser dashboard at `/ui`
- Auto-generates Swagger docs at `/docs`

Battery values are random within a realistic range — `14.0–16.8V` voltage, `60–100%` remaining. This simulates a healthy LiPo pack without needing a real vehicle.

---

## Requirements

- Python 3.11+
- pip

---

## Running Without Docker

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open these in your browser:

| URL | What you see |
|---|---|
| `http://localhost:8000/ui` | Live dashboard |
| `http://localhost:8000/battery` | Raw REST response |
| `http://localhost:8000/docs` | Swagger UI |

The `--reload` flag means uvicorn watches for file changes and restarts automatically — edit `main.py`, save, and the changes apply in about one second without restarting anything.

---

## Running in Docker

Use this to validate the Dockerfile before deploying to the Pi.

```bash
# Build the image
docker build -t battery-monitor:dev .

# Run the container
docker run -d --name battery_monitor -p 8000:8000 battery-monitor:dev

# Watch logs
docker logs -f battery_monitor

# Stop and remove when done
docker rm -f battery_monitor
```

Note: `-p 8000:8000` maps the container port to your laptop. This differs from the Pi deployment which uses `--network host` — see pi-deployment README for why.

---

## File Structure

```
local-dev/
├── main.py           # FastAPI app — simulated get_battery()
├── requirements.txt  # fastapi, uvicorn[standard], websockets
└── Dockerfile
```

---

## How the Simulation Works

`get_battery()` returns random values on every call:

```python
def get_battery() -> dict:
    return {
        "voltage":   round(random.uniform(14.0, 16.8), 2),
        "remaining": random.randint(60, 100),
    }
```

The WebSocket calls this every second and pushes the result to all connected browsers. The REST endpoint calls it once per request. Everything else — routes, WebSocket lifecycle, HTML frontend — is identical to the Pi deployment version.

Swapping simulation for real MAVLink is covered in pi-deployment.

---

## Troubleshooting

**`Could not import module "main"`**
You are running uvicorn from the wrong directory. `cd local-dev` first, then run the command.

**WebSocket not connecting**
Run `pip install "uvicorn[standard]" websockets` — the base uvicorn install does not include WebSocket support.

**Port already in use**
Something else is on 8000. Either stop it or run on a different port:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Container name conflict**
A stopped container with the same name already exists:
```bash
docker rm -f battery_monitor
```
Then re-run the docker run command.
