# CAN MQTT Protocol

This document describes the current MQTT payload format consumed by `server/server.py` and decoded in `server/db_manager.py`.

## Current Frame Payload

The server currently expects each MQTT message payload to be a hexadecimal string of 40 characters. That string decodes to 20 bytes:

```text
Bytes 0-3    CAN ID       uint32, big-endian
Bytes 4-11   timestamp    uint64, big-endian, milliseconds since ESP32 boot
Bytes 12-19  data         8 CAN payload bytes, zero-padded by the firmware
```

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

## Known Ambiguity

The current MQTT format does not include the original CAN DLC. The firmware always sends 8 payload bytes, with shorter CAN payloads zero-padded. Because of that, `CANFrame.from_current_mqtt_payload()` represents current MQTT frames with `dlc=8`.

Future protocol revisions should include the original DLC if the server needs to distinguish real trailing zero bytes from padding.

## Development Checks

Install development dependencies and run the unit tests with:

```powershell
py -m pip install -r requirements-dev.txt
py -m pytest tests
```
