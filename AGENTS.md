# AGENTS.md

## Project Context

This repository contains the Docker-based server stack for Deusto Moto Team / MotoStudent Electric telemetry experiments. The current service receives MQTT messages from an ESP32, decodes CAN frames in Python, and writes time-series data to InfluxDB.

The future direction is robust CAN telemetry ingestion, simulation, tests, and dashboards. Changes should keep that path clean and reviewable.

## Working Rules

- Do not work directly on `main` or `master`; create a feature branch for changes.
- Keep pull requests small, focused, and easy to review.
- Do not commit real credentials, tokens, vehicle data, or track-use secrets.
- Do not introduce live track telemetry features unless explicitly requested by the team.
- Do not implement safety-critical control logic, including contactors, BMS, IMD, charger, inverter, shutdown circuits or throttle/torque commands, without explicit human approval and separate validation by the electronics lead.
- Prefer configuration through `.env` and documented defaults.
- Preserve the current CAN decoding behavior unless the task explicitly asks to change it.
- Add tests when changing parsing, decoding, database writes, or MQTT behavior.

## Repository Shape

- `compose.yaml`: Docker Compose stack for Mosquitto, the Python server, and InfluxDB.
- `mosquitto/config/mosquitto.conf`: local Mosquitto broker configuration.
- `server/server.py`: MQTT subscriber entry point.
- `server/db_manager.py`: CAN frame decoding and InfluxDB writes.
- `server/requirements.txt`: Python runtime dependencies.

## Local Development

1. Copy `.env.example` to `.env`.
2. Replace placeholder secrets in `.env` with local-only values.
3. Start the stack with `docker compose up --build`.
4. Run Python syntax checks before opening a PR:

```bash
python -m py_compile server/server.py server/db_manager.py
```

## Review Checklist

- No real secrets are present in the diff.
- Docker Compose still resolves with `.env` present.
- Python files compile.
- README instructions match the current commands.
