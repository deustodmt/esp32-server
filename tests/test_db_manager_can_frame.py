import pathlib
import sys
import types


SERVER_DIR = pathlib.Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

fake_influxdb_client = types.ModuleType("influxdb_client")
fake_influxdb_client.client = types.ModuleType("influxdb_client.client")
fake_write_api = types.ModuleType("influxdb_client.client.write_api")
fake_write_api.SYNCHRONOUS = object()
sys.modules["influxdb_client"] = fake_influxdb_client
sys.modules["influxdb_client.client"] = fake_influxdb_client.client
sys.modules["influxdb_client.client.write_api"] = fake_write_api

from can_frame import CANFrame
from db_manager import DBManager


def make_manager():
    manager = DBManager.__new__(DBManager)
    writes = []

    def write_point(measurement, timestamp=None, **kwargs):
        writes.append({
            "measurement": measurement,
            "timestamp": timestamp,
            "fields": kwargs,
        })
        return True

    manager.writePoint = write_point
    return manager, writes


def test_db_manager_accepts_current_mqtt_payload_for_ecu_msg1():
    payload = "0CF11E05" + "00000195e0fdc5ee" + "05000000C3010000"
    frame = CANFrame.from_current_mqtt_payload(payload)
    manager, writes = make_manager()

    result = manager.saveCANData(payload)

    assert result is True
    assert frame.can_id == 0x0CF11E05
    assert writes == [{
        "measurement": "ECU",
        "timestamp": None,
        "fields": {
            "RPM": 5,
            "Current": 0.0,
            "Voltage": 45.1,
            "tag_ErrorCode": "0000",
        },
    }]


def test_db_manager_accepts_current_mqtt_payload_for_ecu_msg2_bytes():
    payload = bytes.fromhex("0CF11F05" + "00000195e2c8c5ee" + "2B41330001200000")
    frame = CANFrame.from_current_mqtt_payload(payload)
    manager, writes = make_manager()

    result = manager.saveCANData(payload)

    assert result is True
    assert frame.can_id == 0x0CF11F05
    assert writes == [{
        "measurement": "ECU",
        "timestamp": None,
        "fields": {
            "Throttle": 43,
            "ControllerTemp": 25,
            "MotorTemp": 21,
            "StatusController": 1,
            "SwitchSignals": 32,
        },
    }]


def test_db_manager_preserves_generic_can_raw_write_shape():
    payload = "00000123" + "0000000000000001" + "0102030405060708"
    manager, writes = make_manager()

    result = manager.saveCANData(payload)

    assert result is True
    assert writes == [{
        "measurement": "CAN_raw",
        "timestamp": None,
        "fields": {
            "tag_can_id": "0x00000123",
            "byte0": 1,
            "byte1": 2,
            "byte2": 3,
            "byte3": 4,
            "byte4": 5,
            "byte5": 6,
            "byte6": 7,
            "byte7": 8,
        },
    }]


def test_db_manager_rejects_invalid_current_mqtt_payload_without_writing():
    manager, writes = make_manager()

    result = manager.saveCANData("not-a-can-frame")

    assert result is False
    assert writes == []
