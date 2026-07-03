import argparse
import pathlib
import sys
import time

import paho.mqtt.client as mqtt


SERVER_DIR = pathlib.Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

from can_frame import CANFrame


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 2000
DEFAULT_TOPIC = "test_topic"


def example_frames(timestamp_ms: int) -> list[tuple[str, CANFrame]]:
    return [
        (
            "ecu_msg1",
            CANFrame(
                timestamp=timestamp_ms,
                can_id=0x0CF11E05,
                dlc=8,
                data=(0x05, 0x00, 0x00, 0x00, 0xC3, 0x01, 0x00, 0x00),
                source="simulator",
            ),
        ),
        (
            "ecu_msg2",
            CANFrame(
                timestamp=timestamp_ms + 100,
                can_id=0x0CF11F05,
                dlc=8,
                data=(0x2B, 0x41, 0x33, 0x00, 0x01, 0x20, 0x00, 0x00),
                source="simulator",
            ),
        ),
        (
            "generic",
            CANFrame(
                timestamp=timestamp_ms + 200,
                can_id=0x00000123,
                dlc=8,
                data=(0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08),
                source="simulator",
            ),
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish sample CAN frames using the current MQTT payload format."
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="MQTT broker host")
    parser.add_argument("--port", default=DEFAULT_PORT,
                        type=int, help="MQTT broker port")
    parser.add_argument("--topic", default=DEFAULT_TOPIC,
                        help="MQTT topic to publish")
    parser.add_argument("--interval", default=1.0, type=float,
                        help="Seconds between published frames")
    parser.add_argument("--count", default=1, type=int,
                        help="Number of times to publish the example frame set")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = mqtt.Client(protocol=mqtt.MQTTv5)

    if client.connect(args.host, args.port, 60) != 0:
        print(f"Could not connect to MQTT broker at {args.host}:{args.port}")
        return 1

    try:
        client.loop_start()
        for cycle in range(args.count):
            base_timestamp = int(time.monotonic() * 1000)
            for name, frame in example_frames(base_timestamp):
                payload = frame.to_current_mqtt_payload_hex()
                result = client.publish(args.topic, payload, qos=0)
                result.wait_for_publish()
                print(f"published {name} to {args.topic}: {payload}")
                time.sleep(args.interval)

            if cycle < args.count - 1:
                time.sleep(args.interval)
    finally:
        client.loop_stop()
        client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
