import argparse
import os
from datetime import datetime


DEFAULT_INFLUXDB_URL = "http://localhost:8086"
DEFAULT_INFLUXDB_ORG = "deusto"
DEFAULT_INFLUXDB_BUCKET = "udmt"
DEFAULT_MEASUREMENTS = ("ECU", "CAN_raw")


def flux_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def build_query(bucket: str, measurements: list[str], minutes: int, limit: int) -> str:
    measurement_filter = " or ".join(
        f"r._measurement == {flux_string(measurement)}"
        for measurement in measurements
    )
    return f"""
from(bucket: {flux_string(bucket)})
  |> range(start: -{minutes}m)
  |> filter(fn: (r) => {measurement_filter})
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit})
""".strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query recent telemetry points from InfluxDB."
    )
    parser.add_argument("--url", default=os.getenv(
        "INFLUXDB_URL", DEFAULT_INFLUXDB_URL), help="InfluxDB URL")
    parser.add_argument("--token", default=os.getenv("INFLUXDB_TOKEN"),
                        help="InfluxDB API token")
    parser.add_argument("--org", default=os.getenv(
        "INFLUXDB_ORG", DEFAULT_INFLUXDB_ORG), help="InfluxDB organization")
    parser.add_argument("--bucket", default=os.getenv(
        "INFLUXDB_BUCKET", DEFAULT_INFLUXDB_BUCKET), help="InfluxDB bucket")
    parser.add_argument("--measurement", action="append", choices=DEFAULT_MEASUREMENTS,
                        help="Measurement to query. Can be passed more than once.")
    parser.add_argument("--minutes", default=10, type=int,
                        help="Lookback window in minutes")
    parser.add_argument("--limit", default=20, type=int,
                        help="Maximum number of rows to print")
    return parser.parse_args()


def format_time(value) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def main() -> int:
    args = parse_args()
    if not args.token:
        print("Missing InfluxDB token. Set INFLUXDB_TOKEN or pass --token.")
        return 1
    if args.minutes <= 0:
        print("--minutes must be greater than 0.")
        return 1
    if args.limit <= 0:
        print("--limit must be greater than 0.")
        return 1

    measurements = args.measurement or list(DEFAULT_MEASUREMENTS)
    query = build_query(args.bucket, measurements, args.minutes, args.limit)

    from influxdb_client import InfluxDBClient

    with InfluxDBClient(url=args.url, token=args.token, org=args.org) as client:
        records = list(client.query_api().query_stream(query, org=args.org))

    if not records:
        print("No points found.")
        return 0

    print(f"{'time':<32} {'measurement':<10} {'field':<20} value")
    print("-" * 78)
    for record in records:
        print(
            f"{format_time(record.get_time()):<32} "
            f"{record.get_measurement():<10} "
            f"{record.get_field():<20} "
            f"{record.get_value()}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
