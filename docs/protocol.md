# CAN MQTT Protocol

This document describes the current MQTT payload format consumed by `server/server.py` and decoded in `server/db_manager.py`.

## Current Frame Payload

The binary CAN frame layout is 20 bytes:

```text
Bytes 0-3    CAN ID       uint32, big-endian
Bytes 4-11   timestamp    uint64, big-endian, milliseconds since ESP32 boot
Bytes 12-19  data         8 CAN payload bytes, zero-padded by the firmware
```

The current MQTT transport sends those 20 bytes as a 40-character ASCII/UTF-8 hex string, because `server/server.py` calls `msg.payload.decode()` before passing the payload to `DBManager`.

Example:

```text
0CF11E05 00000195e0fdc5ee 05000000C3010000
```

## CANFrame Mapping

`server/can_frame.py` provides a `CANFrame` model for representing a validated CAN frame before any signal-level decoding is applied.

For the current MQTT format:

- `can_id` comes from bytes 0-3.
- `timestamp` comes from bytes 4-11.
- `data` comes from bytes 12-19.
- `dlc` is set to `8`.
- `source` defaults to `mqtt`.

`CANFrame.to_current_mqtt_payload_bytes()` returns the 20 binary bytes. `CANFrame.to_current_mqtt_payload_hex()` returns the 40-character uppercase hex string that the current server expects over MQTT.

## Known Ambiguity

The current MQTT format does not include the original CAN DLC. The firmware always sends 8 payload bytes, with shorter CAN payloads zero-padded. Because of that, `CANFrame.from_current_mqtt_payload()` represents current MQTT frames with `dlc=8`.

Future protocol revisions should include the original DLC if the server needs to distinguish real trailing zero bytes from padding.

## Development Checks

Install development dependencies and run the unit tests with:

```powershell
py -m pip install -r requirements-dev.txt
py -m pytest tests
```

## Local MQTT Simulator

The repository includes a small local simulator for publishing sample frames without an ESP32. It publishes to the current server topic, `test_topic`, by default.

The simulator publishes the 40-character hex string, not raw binary bytes, to match the current `server.py` behavior.

Start the Docker stack first:

```powershell
docker compose up --build
```

In another terminal, install the Python runtime dependency used by the simulator and publish one set of sample frames:

```powershell
py -m pip install -r server/requirements.txt
py tools\publish_mqtt_frames.py --host localhost --port 2000 --topic test_topic
```

The simulator publishes:

- ECU message 1 (`0x0CF11E05`)
- ECU message 2 (`0x0CF11F05`)
- one generic/unknown CAN frame

Use `--interval` to control the delay between frames and `--count` to repeat the sample set.
