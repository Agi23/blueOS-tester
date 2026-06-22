# pi-deployment

Deploys the battery monitor to the Raspberry Pi running on the BlueROV2. Reads real battery telemetry from ArduSub via the BlueOS MAVLink router.

Assumes BlueOS is running and the vehicle is powered. Test with local-dev first.

---

## What Changes From local-dev

Only two things are different:

| | local-dev | pi-deployment |
|---|---|---|
| Data source | `random.uniform()` | `BATTERY_STATUS` MAVLink message |
| MAVLink connection | none | `udp:localhost:14550` |
| Docker network | `-p 8000:8000` | `--network host` |
| WebSocket URL | `ws://localhost:8000` | `ws://` + `location.host` |

The FastAPI routes, WebSocket stream, and HTML frontend are identical.

---

## Prerequisites

- BlueOS running and accessible at `blueos.local`
- ROV powered and ArduSub connected to BlueOS
- SSH access to the Pi (`ssh pi@blueos.local`)

Confirm BlueOS is reachable before starting:

```bash
ping blueos.local
```

---

## Deploy Steps

### 1. SSH into the Pi

```bash
ssh pi@blueos.local
# Default password: raspberry
```

### 2. Get the code onto the Pi

```bash
# Option A: clone from GitHub
git clone https://github.com/Agi23/blueOS-tester.git
cd blueOS-tester/pi-deployment

# Option B: SCP from your laptop (run on your laptop, not the Pi)
scp -r ./pi-deployment pi@blueos.local:/home/pi/
```

### 3. Build the image on the Pi

```bash
docker build -t battery-monitor:dev .
```

Build takes a few minutes the first time — pip installing on ARM is slower than on a laptop. Subsequent builds use the cache and are much faster.

### 4. Run the container

```bash
docker run -d \
  --name battery_monitor \
  --network host \
  --restart unless-stopped \
  battery-monitor:dev
```

### 5. Check it started correctly

```bash
docker logs -f battery_monitor
```

Expected output:

```
Waiting for MAVLink heartbeat...
Heartbeat received from system 1
INFO:     Uvicorn running on http://0.0.0.0:8000
```

If it hangs on "Waiting for MAVLink heartbeat" the vehicle is not connected or ArduSub is not running. Confirm the ROV is powered and check with your team.

---

## Verify It Is Working

Open these from your laptop browser:

| URL | What you see |
|---|---|
| `http://blueos.local:8000/ui` | Live dashboard with real values |
| `http://blueos.local:8000/battery` | Raw JSON response |
| `http://blueos.local:8000/docs` | Swagger UI |

Cross-check voltage against BlueOS:

```
blueos.local → Autopilot → Battery
```

Your extension and BlueOS should show the same voltage within a few millivolts. If your extension shows `0V` or `-1%` remaining, the MAVLink connection is not working — see troubleshooting below.

---

## Why `--network host`

On Linux (the Pi), `--network host` makes the container share the Pi's network namespace. This means `localhost` inside the container refers to the Pi itself, not the container. Without it, `udp:localhost:14550` would try to reach the MAVLink router inside the container — where nothing is listening.

On Windows Docker Desktop this flag does not behave the same way, which is why local-dev uses `-p 8000:8000` instead.

---

## How the MAVLink Connection Works

```python
mav = mavutil.mavlink_connection('udp:localhost:14550')
mav.wait_heartbeat()
```

BlueOS Core runs a MAVLink Router service that receives messages from ArduSub and rebroadcasts them to all configured listeners on port 14550. `wait_heartbeat()` blocks until ArduSub sends a HEARTBEAT message, confirming the vehicle is alive. Only then does the FastAPI server start accepting requests.

Battery data comes from the `BATTERY_STATUS` message:

```python
msg = mav.recv_match(type='BATTERY_STATUS', blocking=True, timeout=3.0)
voltage = msg.voltages[0] / 1000   # MAVLink sends millivolts
```

---

## Iterating on Code (Without Rebuilding the Image)

For fast development on the Pi, run with a volume mount so code changes apply immediately:

```bash
docker run -d \
  --name battery_monitor \
  --network host \
  -v /home/pi/blueOS-tester/pi-deployment:/app \
  battery-monitor:dev
```

Edit files on the Pi via Remote-SSH in VSCode. Uvicorn detects changes and reloads automatically. Only rebuild the image when `requirements.txt` or the `Dockerfile` itself changes.

---

## Stopping and Removing

```bash
# Stop without removing (can restart later)
docker stop battery_monitor

# Remove entirely
docker rm -f battery_monitor
```

The `--restart unless-stopped` flag means the container comes back after a Pi reboot, but stays stopped if you manually stop it.

---

## Troubleshooting

**Hangs on "Waiting for MAVLink heartbeat"**
ArduSub is not running or not connected to BlueOS. Confirm the ROV is powered and the autopilot shows as connected in the BlueOS web UI.

**Container exits immediately after starting**
Check logs:
```bash
docker logs battery_monitor
```
Common cause: build error due to missing C compiler for pymavlink on ARM. Fix by adding to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y gcc && pip install -r requirements.txt
```
Then rebuild.

**Voltage reads 0V or remaining reads -1**
MAVLink is connected (heartbeat received) but no BATTERY_STATUS messages are arriving. Confirm the battery is connected to the vehicle and ArduSub is reporting battery data in QGroundControl or Cockpit.

**Port 8000 already in use**
Another container or service is using port 8000. Check:
```bash
docker ps
ss -tulnp | grep 8000
```

**Container name conflict**
```bash
docker rm -f battery_monitor
```
Then re-run the docker run command.
