import struct
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
        
    
    def writePoint(self, measurement:str, timestamp:int = None,**kwargs):
        """
        Writes a point to the InfluxDB database
        The format is as follows:
        Measurement: <measurement>
        Tag: tag_<tag_name> = <tag_value> // The tag_ will be removed when writing the tag
        Field: <field_name> = <field_value>
        """
        try:
            p = influxdb_client.Point(measurement)

            # MotoStudent Bike Signature
            p.tag("Moto", "moto_student_2025")

            if timestamp is not None:
                # if(len(timestamp) != 8 ):
                #     print(f"Error, timestamp format is not 8 byte: {timestamp}")
                #     return False
                # else:
                p.time(timestamp, write_precision="ms")

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
        
    def saveCANData(self, data):
        """
        Decodifies the CAN data and saves it to the database
        Format of the data (20 bytes):
        0-3: ID
        4-11: Timestamp
        12-19: Data
        """

        if isinstance(data, str):
            try:
                data = bytes.fromhex(data)
                print(data)
            except ValueError:
                print(f"Error: Invalid hex string, data: {data}")
                return False
        
        if len(data) != 20:
            print(f"Error: Invalid data length ({len(data)} bytes). Expected 20 bytes.")
            return False

        try:
            ID = struct.unpack(">I", data[0:4])[0]
            timestamp = struct.unpack(">Q", data[4:12])[0]  #If the timestamp is not recent, the message will not be added to the db
            segmentData = []    # List of payload bytes like in the documentation [1, 2, 3, 4, 5, 6, 7, 8]

            for i in range(12, 20):
                segmentData.append(struct.unpack(">B", data[i:i+1])[0])

            if(ID == ECU_ID_MSG1):
                self.writePoint("ECU",
                                # timestamp,
                                RPM=segmentData[1]*256+segmentData[0], 
                                Current=(segmentData[3]*256+segmentData[2])/10,
                                Voltage=(segmentData[5]*256+segmentData[4])/10,
                                tag_ErrorCode=data[18:20].hex().upper()
                                )
                print("MSG ECU 1 OK")
            elif(ID == ECU_ID_MSG2):
                self.writePoint("ECU", 
                                # timestamp,
                                Threottle=segmentData[0],
                                ControllerTemp=segmentData[1] - 40,
                                MotorTemp=segmentData[2] - 30,
                                StatusController=segmentData[4],
                                SwitchSignals=segmentData[5],
                                )
                print("MSG ECU 2 OK")
            else:
                print("Error: Incorrect ID")
                return False
            return True
        
        except Exception as e:
            print(f"Error message not saved, error_code: {e}\nData forat is: {data}")
            return False

