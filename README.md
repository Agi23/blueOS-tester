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

## Getting the Code

### Clone the repo on your laptop

```bash
git clone https://github.com/Agi23/blueOS-tester.git
cd blueOS-tester
```

### Get the code onto the Pi

**Using git clone**

```bash
ssh pi@blueos.local
git clone https://github.com/Agi23/blueOS-tester.git
cd blueOS-tester/pi-deployment
```

Any future updates are a single `git pull` on the Pi — no file transfer needed.

## Quick Start

### local-dev: Run with uvicorn (no Docker)

The fastest way to get started — no hardware or Docker required.

```bash
cd local-dev
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser:

| URL | What you see |
|---|---|
| `http://localhost:8000/ui` | Live dashboard (simulated values) |
| `http://localhost:8000/battery` | Raw REST response |
| `http://localhost:8000/docs` | Swagger UI |

The `--reload` flag means any file change restarts the server automatically — no manual intervention needed.

---

### local-dev: Test the Docker container

Use this to validate the Dockerfile before deploying to the Pi.

```bash
cd local-dev

# Build
docker build -t battery-monitor:dev .

# Run
docker run -d --name battery_monitor -p 8000:8000 battery-monitor:dev

# Check it started
docker logs -f battery_monitor

# Open http://localhost:8000/ui

# Clean up when done
docker rm -f battery_monitor
```

Note: uses `-p 8000:8000` port mapping rather than `--network host` — this is correct for Docker Desktop on Windows/Mac. The Pi deployment uses `--network host` instead; see pi-deployment README for why.

---

### pi-deployment: Deploy to the BlueROV2

```bash
# SSH into the Pi
ssh pi@blueos.local

cd /home/pi/blueOS-tester/pi-deployment

# Build on the Pi (required — laptop image won't run on ARM)
docker build -t battery-monitor:dev .

# Run
docker run -d \
  --name battery_monitor \
  --network host \
  --restart unless-stopped \
  battery-monitor:dev

# Confirm MAVLink heartbeat received and server is up
docker logs -f battery_monitor
```

Open `http://blueos.local:8000/ui` from your laptop browser.

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