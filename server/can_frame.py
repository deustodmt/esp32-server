from dataclasses import dataclass


CAN_CLASSIC_MAX_ID = 0x7FF
CAN_EXTENDED_MAX_ID = 0x1FFFFFFF
UINT64_MAX = 0xFFFFFFFFFFFFFFFF
CURRENT_MQTT_FRAME_LENGTH_BYTES = 20
CURRENT_MQTT_PAYLOAD_DLC = 8


@dataclass(frozen=True)
class CANFrame:
    timestamp: int
    can_id: int
    dlc: int
    data: tuple[int, ...]
    source: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.timestamp, bool) or not isinstance(self.timestamp, int):
            raise TypeError("timestamp must be an integer")
        if self.timestamp < 0:
            raise ValueError("timestamp must be non-negative")
        if self.timestamp > UINT64_MAX:
            raise ValueError("timestamp must fit in an unsigned 64-bit integer")

        if isinstance(self.can_id, bool) or not isinstance(self.can_id, int):
            raise TypeError("can_id must be an integer")
        if not 0 <= self.can_id <= CAN_EXTENDED_MAX_ID:
            raise ValueError("can_id must be in the CAN classic or extended range")

        if isinstance(self.dlc, bool) or not isinstance(self.dlc, int):
            raise TypeError("dlc must be an integer")
        if not 0 <= self.dlc <= CURRENT_MQTT_PAYLOAD_DLC:
            raise ValueError("dlc must be between 0 and 8 for classic CAN")

        data = tuple(self.data)
        if len(data) != self.dlc:
            raise ValueError("data length must match dlc")
        for byte in data:
            if isinstance(byte, bool) or not isinstance(byte, int):
                raise TypeError("data bytes must be integers")
            if not 0 <= byte <= 0xFF:
                raise ValueError("data bytes must be between 0 and 255")

        object.__setattr__(self, "data", data)

    @property
    def is_extended_id(self) -> bool:
        return self.can_id > CAN_CLASSIC_MAX_ID

    @classmethod
    def from_current_mqtt_payload(
        cls,
        payload: str | bytes | bytearray,
        *,
        source: str | None = "mqtt",
    ) -> "CANFrame":
        raw = _coerce_current_mqtt_payload(payload)
        can_id = int.from_bytes(raw[0:4], byteorder="big", signed=False)
        timestamp = int.from_bytes(raw[4:12], byteorder="big", signed=False)
        data = tuple(raw[12:20])

        return cls(
            timestamp=timestamp,
            can_id=can_id,
            dlc=CURRENT_MQTT_PAYLOAD_DLC,
            data=data,
            source=source,
        )

    def to_current_mqtt_payload_bytes(self) -> bytes:
        if self.dlc != CURRENT_MQTT_PAYLOAD_DLC:
            raise ValueError("current MQTT payload format requires dlc=8")

        return (
            self.can_id.to_bytes(4, byteorder="big", signed=False)
            + self.timestamp.to_bytes(8, byteorder="big", signed=False)
            + bytes(self.data)
        )

    def to_current_mqtt_payload_hex(self) -> str:
        return self.to_current_mqtt_payload_bytes().hex().upper()

    def to_current_mqtt_payload(self) -> str:
        """Return the text hex payload that server.py currently expects over MQTT."""
        return self.to_current_mqtt_payload_hex()


def _coerce_current_mqtt_payload(payload: str | bytes | bytearray) -> bytes:
    if isinstance(payload, str):
        try:
            raw = bytes.fromhex(payload.strip())
        except ValueError as exc:
            raise ValueError("MQTT payload must be a hex string") from exc
    elif isinstance(payload, (bytes, bytearray)):
        raw = bytes(payload)
    else:
        raise TypeError("MQTT payload must be a hex string or bytes")

    if len(raw) != CURRENT_MQTT_FRAME_LENGTH_BYTES:
        raise ValueError("MQTT payload must decode to exactly 20 bytes")

    return raw
