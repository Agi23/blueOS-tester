# BlueOS Battery Monitor

A minimal BlueOS extension that reads battery telemetry from a BlueROV2 and streams it live to a browser dashboard via REST and WebSocket.

Built as a learning exercise to understand the relationship between MAVLink, the BlueOS extension architecture, Docker, and the REST/WebSocket communication patterns used in BlueOS microservices.

---

## Project Structure

```
blueOS-tester/
├── local-dev/          # Runs on any laptop — no hardware required
│   ├── main.py         # FastAPI app with simulated battery values
│   ├── requirements.txt
│   └── Dockerfile
│
└── pi-deployment/      # Deploys to Raspberry Pi on the ROV
    ├── main.py         # FastAPI app with real MAVLink connection
    ├── requirements.txt
    └── Dockerfile
```

---

## Architecture

```
MAVLink Router (BlueOS Core)
    │  udp:localhost:14550
    ▼
FastAPI backend (this extension)
    ├── GET /battery       →  single REST snapshot
    ├── WS  /ws/battery    →  1Hz live stream (pub/sub)
    └── GET /ui            →  browser dashboard
              │
              ▼
         Browser (standalone or Cockpit iframe widget)
```

The REST endpoint handles on-demand queries — initial page load, external services, Swagger testing. The WebSocket handles continuous streaming — the server pushes updates without the client polling. These are two different communication patterns used for different purposes; see the individual READMEs for detail.

---

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/battery` | GET | Current battery snapshot |
| `/ws/battery` | WS | Live 1Hz stream |
| `/ui` | GET | Browser dashboard |
| `/docs` | GET | Auto-generated Swagger UI |

---

## Quick Start

### No hardware (local-dev)

```bash
cd local-dev
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000/ui`

### On the BlueROV2 Pi (pi-deployment)

```bash
# SSH into the Pi first
ssh pi@blueos.local
cd /home/pi/blueOS-tester/pi-deployment
docker build -t battery-monitor:dev .
docker run -d --name battery_monitor --network host --restart unless-stopped battery-monitor:dev
```

Open `http://blueos.local:8000/ui`

---

## Key Learning Points

- The only difference between local-dev and pi-deployment is the MAVLink connection string and the data source — the FastAPI routes, WebSocket, and frontend are identical
- Volume mounts during development mean you can edit code without rebuilding the Docker image
- `--network host` on the Pi gives the container access to the MAVLink router on `localhost:14550`
- BlueOS extensions are just Docker containers with a `metadata.json` that tells BlueOS how to run them
