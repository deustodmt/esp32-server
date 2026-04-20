import struct
import influxdb_client
import os
from influxdb_client.client.write_api import SYNCHRONOUS

# ── Known ECU message IDs ────────────────────────────────────────────────────
ECU_ID_MSG1 = 0x0CF11E05    # RPM, Current, Voltage, ErrorCode
ECU_ID_MSG2 = 0x0CF11F05    # Throttle, Temps, Status, Switches


class DBManager:
    def __init__(self, bucket):
        self.bucket = bucket
        self.org = os.getenv("INFLUXDB_ORG",   "deusto")
        self.token = os.getenv("INFLUXDB_TOKEN",  "udmt_super_secure_token")
        self.url = os.getenv("INFLUXDB_URL",    "http://db:8086")
        try:
            self.client = influxdb_client.InfluxDBClient(
                url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        except Exception as e:
            print(f"Error al conectar con InfluxDB: {e}")
            self.client = None
            self.write_api = None

    # ── Low-level write helper ───────────────────────────────────────────────
    def writePoint(self, measurement: str, timestamp: int = None, **kwargs):
        """
        Writes a point to InfluxDB.
        kwargs prefixed with 'tag_' are stored as tags (prefix stripped).
        All other kwargs are stored as fields.
        """
        try:
            p = influxdb_client.Point(measurement)
            p.tag("Moto", "moto_student_2025")

            if timestamp is not None:
                p.time(timestamp, write_precision="ms")

            for key, val in kwargs.items():
                if key.startswith("tag_"):
                    p.tag(key[4:], val)
                else:
                    p.field(key, val)

            self.write_api.write(bucket=self.bucket, org=self.org, record=p)
            return True
        except Exception as e:
            print(f"Error al crear el punto: {e}")
            return False

    # ── Main entry point ─────────────────────────────────────────────────────
    def saveCANData(self, data):
        """
        Decodes a CAN frame and writes it to InfluxDB.

        Expected wire format (20 bytes, transmitted as a 40-char hex string):
          Bytes  0- 3 : CAN ID        (uint32, big-endian)
          Bytes  4-11 : timestamp_ms  (uint64, big-endian)
                        upper 4 bytes are 0; lower 4 bytes = ESP32 millis()
          Bytes 12-19 : payload       (8 bytes, zero-padded to full length)

        This matches the packForServer() output in the ESP32 can-monitor firmware.
        """

        # ── Accept hex string or raw bytes ───────────────────────────────────
        if isinstance(data, str):
            data = data.strip()
            try:
                data = bytes.fromhex(data)
            except ValueError:
                print(f"Error: cadena hex inválida — '{data}'")
                return False

        if len(data) != 20:
            print(f"Error: longitud inválida ({
                  len(data)} bytes). Se esperaban 20.")
            return False

        try:
            can_id = struct.unpack(">I", data[0:4])[0]
            timestamp = struct.unpack(">Q", data[4:12])[
                0]   # ms since ESP32 boot
            payload = list(data[12:20])                    # 8 decoded bytes

            print(f"CAN  ID=0x{can_id:08X}  ts={timestamp}ms  payload={
                  [f'{b:02X}' for b in payload]}")

            # ── Dispatch by CAN ID ───────────────────────────────────────────
            if can_id == ECU_ID_MSG1:
                return self._handle_ecu_msg1(payload, timestamp)

            elif can_id == ECU_ID_MSG2:
                return self._handle_ecu_msg2(payload, timestamp)

            else:
                # [MODIFIED] Generic handler — stores raw payload for any unknown ID.
                # Add specific decoders above (like _handle_ecu_msg1) as needed.
                return self._handle_generic(can_id, payload, timestamp)

        except Exception as e:
            print(f"Error procesando trama: {e}  data={data.hex().upper()}")
            return False

    # ── Per-ID decoders ──────────────────────────────────────────────────────

    def _handle_ecu_msg1(self, payload, timestamp):
        """ECU message 1: RPM, Current, Voltage, ErrorCode."""
        result = self.writePoint(
            "ECU",
            # timestamp,                          # uncomment to use ESP32 time
            RPM=payload[1] * 256 + payload[0],
            Current=(payload[3] * 256 + payload[2]) / 10,
            Voltage=(payload[5] * 256 + payload[4]) / 10,
            tag_ErrorCode=f"{payload[6]:02X}{payload[7]:02X}",
        )
        if result:
            print("MSG ECU 1 OK")
        return result

    def _handle_ecu_msg2(self, payload, timestamp):
        """ECU message 2: Throttle, temperatures, status flags."""
        result = self.writePoint(
            "ECU",
            # timestamp,
            Throttle=payload[0],
            ControllerTemp=payload[1] - 40,
            MotorTemp=payload[2] - 30,
            StatusController=payload[4],
            SwitchSignals=payload[5],
        )
        if result:
            print("MSG ECU 2 OK")
        return result

    def _handle_generic(self, can_id, payload, timestamp):
        """
        [ADDED] Fallback handler for CAN IDs not yet mapped to a specific decoder.
        Stores the raw payload bytes as individual fields (byte0..byte7) under
        the measurement 'CAN_raw', tagged with the frame ID.
        Add a dedicated _handle_* method above when you know the signal layout.
        """
        fields = {f"byte{i}": payload[i] for i in range(8)}
        result = self.writePoint(
            "CAN_raw",
            # timestamp,
            tag_can_id=f"0x{can_id:08X}",
            **fields,
        )
        if result:
            print(f"MSG GENERIC 0x{can_id:08X} OK")
        return result
