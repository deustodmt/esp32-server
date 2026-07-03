import pathlib
import sys

import pytest


SERVER_DIR = pathlib.Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

from can_frame import CAN_EXTENDED_MAX_ID, CANFrame


def test_can_frame_accepts_valid_classic_frame():
    frame = CANFrame(timestamp=1234, can_id=0x123, dlc=3, data=[1, 2, 3])

    assert frame.timestamp == 1234
    assert frame.can_id == 0x123
    assert frame.dlc == 3
    assert frame.data == (1, 2, 3)
    assert frame.source is None
    assert frame.is_extended_id is False


def test_can_frame_accepts_valid_extended_frame():
    frame = CANFrame(
        timestamp=0,
        can_id=CAN_EXTENDED_MAX_ID,
        dlc=8,
        data=[0, 1, 2, 3, 4, 5, 6, 255],
        source="mqtt",
    )

    assert frame.is_extended_id is True
    assert frame.source == "mqtt"


def test_timestamp_must_be_non_negative():
    with pytest.raises(ValueError, match="timestamp"):
        CANFrame(timestamp=-1, can_id=0x123, dlc=0, data=[])


def test_timestamp_must_reject_bool():
    with pytest.raises(TypeError, match="timestamp"):
        CANFrame(timestamp=True, can_id=0x123, dlc=0, data=[])


def test_can_id_must_be_integer():
    with pytest.raises(TypeError, match="can_id"):
        CANFrame(timestamp=0, can_id="0x123", dlc=0, data=[])


def test_can_id_must_reject_bool():
    with pytest.raises(TypeError, match="can_id"):
        CANFrame(timestamp=0, can_id=True, dlc=0, data=[])


@pytest.mark.parametrize("can_id", [-1, CAN_EXTENDED_MAX_ID + 1])
def test_can_id_must_be_in_valid_can_range(can_id):
    with pytest.raises(ValueError, match="can_id"):
        CANFrame(timestamp=0, can_id=can_id, dlc=0, data=[])


def test_dlc_must_reject_bool():
    with pytest.raises(TypeError, match="dlc"):
        CANFrame(timestamp=0, can_id=0x123, dlc=True, data=[1])


@pytest.mark.parametrize("dlc", [-1, 9])
def test_dlc_must_be_classic_can_length(dlc):
    with pytest.raises(ValueError, match="dlc"):
        CANFrame(timestamp=0, can_id=0x123, dlc=dlc, data=[])


def test_data_length_must_match_dlc():
    with pytest.raises(ValueError, match="data length"):
        CANFrame(timestamp=0, can_id=0x123, dlc=2, data=[1])


@pytest.mark.parametrize("byte", [-1, 256])
def test_data_bytes_must_be_byte_values(byte):
    with pytest.raises(ValueError, match="data bytes"):
        CANFrame(timestamp=0, can_id=0x123, dlc=1, data=[byte])


def test_data_bytes_must_reject_bool():
    with pytest.raises(TypeError, match="data bytes"):
        CANFrame(timestamp=0, can_id=0x123, dlc=1, data=[False])


def test_current_mqtt_payload_hex_string_is_parsed():
    frame = CANFrame.from_current_mqtt_payload(
        "0CF11E05" + "00000195e0fdc5ee" + "05000000C3010000"
    )

    assert frame.can_id == 0x0CF11E05
    assert frame.timestamp == 0x00000195E0FDC5EE
    assert frame.dlc == 8
    assert frame.data == (0x05, 0x00, 0x00, 0x00, 0xC3, 0x01, 0x00, 0x00)
    assert frame.source == "mqtt"


def test_current_mqtt_payload_bytes_are_parsed_with_custom_source():
    payload = bytes.fromhex("0CF11F05" + "00000195e2c8c5ee" + "2B41330001200000")

    frame = CANFrame.from_current_mqtt_payload(payload, source="test")

    assert frame.can_id == 0x0CF11F05
    assert frame.timestamp == 0x00000195E2C8C5EE
    assert frame.dlc == 8
    assert frame.data == (0x2B, 0x41, 0x33, 0x00, 0x01, 0x20, 0x00, 0x00)
    assert frame.source == "test"


def test_current_mqtt_payload_rejects_non_hex_string():
    with pytest.raises(ValueError, match="hex string"):
        CANFrame.from_current_mqtt_payload("not-a-can-frame")


def test_current_mqtt_payload_rejects_wrong_decoded_length():
    with pytest.raises(ValueError, match="20 bytes"):
        CANFrame.from_current_mqtt_payload("00")
