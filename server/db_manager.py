import influxdb_client, os
from influxdb_client.client.write_api import SYNCHRONOUS

class DBManager:
    def __init__(self, bucket):
        self.bucket = bucket
        self.org = os.getenv("INFLUXDB_ORG", "myorg")
        self.token = os.getenv("INFLUXDB_TOKEN", "mytoken")
        self.url = os.getenv("INFLUXDB_URL", "http://db:8086")

        try:
            self.client = influxdb_client.InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        except Exception as e:
            print(f"Error al conectar con InfluxDB: {e}")
            self.client = None
            self.write_api = None
    
    def writeTest(self):
        try:
            p = influxdb_client.Point("my_measurement").tag("location", "Prague").field("temperature", 25.3)
            self.write_api.write(bucket = self.bucket, org = self.org, record=p)
        except Exception as e:
            print(f"Error al crear el punto: {e}")
            return
