import influxdb_client, os
from influxdb_client.client.write_api import SYNCHRONOUS

ECU_ID_MSG1 = 0x0CF11E05    # ID del mensaje 1 del ECU
ECU_ID_MSG2 = 0x0CF11F05    # ID del mensaje 2 del ECU

class DBManager:
    def __init__(self, bucket):
        self.bucket = bucket
        self.org = os.getenv("INFLUXDB_ORG", "deusto")
        self.token = os.getenv("INFLUXDB_TOKEN", "udmt_super_secure_token")
        self.url = os.getenv("INFLUXDB_URL", "http://db:8086")
        print(ECU_ID_MSG1.to_bytes(4, byteorder='big')[0:3])
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
        
    
    def writePoint(self, measurement:str, **kwargs):
        """
        Writes a point to the InfluxDB database
        The format is as follows:
        Measurement: <measurement>
        Tag: tag_<tag_name> = <tag_value> // The tag_ will be removed when writing the tag
        Field: <field_name> = <field_value>
        """
        try:
            p = influxdb_client.Point(measurement)
            for key in kwargs:
                if key.startswith("tag_"):
                    p.tag(key[4:], kwargs[key])
                else:
                    p.field(key, kwargs[key])
            self.write_api.write(bucket = self.bucket, org = self.org, record=p)
            return True
        
        except Exception as e:
            print(f"Error al crear el punto: {e}")
            return False
        
    def saveCANData(self, data:str):
        """
        Decodifies the CAN data and saves it to the database
        Format of the data (16 bytes):
        0-3: ID
        4-7: Timestamp
        8-15: Data
        """
        if(len(data) != 16):
            print("Error: La longitud de los datos no es correcta")
            return False
        
        try:
            if(data[0:3] == ECU_ID_MSG1.to_bytes(4, byteorder='big')[0:3]):
                self.writePoint("ECU", 
                                RPM=1, 
                                tag_ID=1, 
                                #timestamp=int.from_bytes(data[4:7], "big"), 
                                #data=int.from_bytes(data[8:15], "big")
                                )
                print("Datos guardados correctamente")
            elif(data[0:3] == ECU_ID_MSG2):
                self.writePoint("ECU", 
                                tag_ECU="2", 
                                tag_ID="2", 
                                timestamp=int.from_bytes(data[4:7], "big"), 
                                data=int.from_bytes(data[8:15], "big"))
                print("Datos guardados correctamente 2")
            else:
                print("Error: ID incorrecto")
                return False
            return True
        
        except Exception as e:
            print(f"Error al guardar los datos en la base de datos: {e}")
            return False

