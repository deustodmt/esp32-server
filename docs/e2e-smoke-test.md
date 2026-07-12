# End-to-End Smoke Test

Use this guide to validate the local flow without an ESP32:

```text
MQTT/CAN simulator -> Mosquitto -> esp32-server -> InfluxDB
```

This is a local bench/development check only. It is not live track telemetry.
Running this smoke test requires Docker with Docker Compose available. This guide
describes how to validate the flow locally; it does not claim that the end-to-end
test has already been executed successfully on every development machine.

## 1. Prepare Environment

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Review `.env` and keep these values aligned unless you intentionally change them:

```dotenv
MQTT_TOPIC=test_topic
INFLUXDB_ORG=deusto
INFLUXDB_BUCKET=udmt
INFLUXDB_TOKEN=change-me-local-token
```

## 2. Start The Stack

```powershell
docker compose up --build
```

Wait until Mosquitto, InfluxDB, and `esp32-server` are running. The Python server should subscribe to the configured MQTT topic.

## 3. Publish Simulated CAN Frames

In another terminal, install the Python runtime dependencies used by the tools:

```powershell
py -m pip install -r server/requirements.txt
```

Publish five sets of sample frames to the default local Mosquitto port and topic:

```powershell
py tools\publish_mqtt_frames.py --host localhost --port 2000 --topic test_topic --count 5
```

The simulator publishes:

- ECU message 1 (`0x0CF11E05`)
- ECU message 2 (`0x0CF11F05`)
- one generic/unknown CAN frame

If you changed `MQTT_TOPIC` in `.env`, pass the same topic with `--topic`.

## 4. Check Server Logs

In the `docker compose up --build` terminal, confirm that `esp32-server` logs received CAN frames and successful handlers such as:

```text
MSG ECU 1 OK
MSG ECU 2 OK
MSG GENERIC 0x00000123 OK
```

## 5. Check InfluxDB UI

Open InfluxDB:

```text
http://localhost:8086
```

Use the credentials and organization from `.env`. The default bucket is `udmt`.

Expected measurements:

- `ECU`
- `CAN_raw`

## 6. Query Recent Points From Console

Set the local InfluxDB connection values:

```powershell
$env:INFLUXDB_URL="http://localhost:8086"
$env:INFLUXDB_TOKEN="change-me-local-token"
$env:INFLUXDB_ORG="deusto"
$env:INFLUXDB_BUCKET="udmt"
```

Query recent ECU points:

```powershell
py tools\query_recent_points.py --measurement ECU --minutes 10
```

Query recent generic CAN points:

```powershell
py tools\query_recent_points.py --measurement CAN_raw --minutes 10
```

The query tool is read-only. It does not publish MQTT messages and does not modify InfluxDB data.
