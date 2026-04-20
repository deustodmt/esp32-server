# esp32-server

Stack de servidor para recibir, decodificar y almacenar telemetría CAN enviada por el firmware **esp32-can-monitor** a través de MQTT.

## Descripción general

El sistema consta de tres servicios Docker orquestados con Compose:

- **Mosquitto** — broker MQTT que recibe los mensajes del ESP32
- **esp32-server** — servicio Python que suscribe el topic MQTT, decodifica las tramas CAN y las escribe en InfluxDB
- **InfluxDB** — base de datos de series temporales donde se almacenan los datos

## Arquitectura

```
ESP32 (firmware)
    │  MQTT (topic: test_topic)
    ▼
Mosquitto :2000 (externo) / :1883 (interno Docker)
    │  MQTT (topic: test_topic)
    ▼
esp32-server (Python)
    │  InfluxDB client
    ▼
InfluxDB :8086
    │
    ▼
Grafana / consultas externas
```

## Requisitos

- Docker y Docker Compose

## Puesta en marcha

```bash
docker compose up --build
```

Los servicios arrancan en orden: primero Mosquitto y InfluxDB (con healthchecks), y solo cuando están listos arranca el servidor Python.

## Servicios y puertos

| Servicio | Puerto externo | Puerto interno | Descripción |
|---|---|---|---|
| Mosquitto | 2000 | 1883 | Broker MQTT. El ESP32 conecta al puerto 2000 |
| InfluxDB | 8086 | 8086 | Base de datos. UI web accesible en `http://localhost:8086` |

## Configuración InfluxDB

| Parámetro | Valor por defecto |
|---|---|
| Organización | `deusto` |
| Bucket | `udmt` |
| Usuario admin | `admin` / `adminadmin` |
| Token | `udmt_super_secure_token` |

Los datos persistentes de InfluxDB se guardan en `./db/data/`.

## Formato de mensajes esperado

El servidor recibe strings hexadecimales de 40 caracteres (= 20 bytes) publicados por el ESP32 en el topic `test_topic`. El layout es:

```
Bytes  0- 3: CAN ID      (uint32, big-endian)
Bytes  4-11: timestamp   (uint64, big-endian, millis desde arranque ESP32)
Bytes 12-19: payload CAN (8 bytes, zero-padded)
```

Este formato es el generado por `packForServer()` en el firmware esp32-can-monitor.

## Decodificación de tramas CAN (`server/db_manager.py`)

El servidor reconoce los siguientes CAN IDs específicos de la ECU:

### `0x0CF11E05` — ECU Mensaje 1

| Campo | Bytes payload | Decodificación | Unidad |
|---|---|---|---|
| RPM | 0-1 | `byte[1]*256 + byte[0]` | rpm |
| Current | 2-3 | `(byte[3]*256 + byte[2]) / 10` | A |
| Voltage | 4-5 | `(byte[5]*256 + byte[4]) / 10` | V |
| ErrorCode | 6-7 | hex string (tag InfluxDB) | — |

Measurement InfluxDB: `ECU`

### `0x0CF11F05` — ECU Mensaje 2

| Campo | Byte payload | Decodificación | Unidad |
|---|---|---|---|
| Throttle | 0 | valor directo | % |
| ControllerTemp | 1 | `byte - 40` | °C |
| MotorTemp | 2 | `byte - 30` | °C |
| StatusController | 4 | valor directo | — |
| SwitchSignals | 5 | valor directo | — |

Measurement InfluxDB: `ECU`

### IDs desconocidos — handler genérico

Cualquier trama con un CAN ID no reconocido se almacena con los 8 bytes del payload como campos individuales (`byte0`..`byte7`) bajo el measurement `CAN_raw`, con el ID como tag (`can_id`).

Para añadir soporte a nuevos IDs, crear un método `_handle_ecu_msgX()` en `db_manager.py` y añadir el CAN ID correspondiente al bloque de dispatch en `saveCANData()`.

## Variables de entorno (`server/db_manager.py`)

El servidor Python lee la configuración de InfluxDB desde las siguientes variables de entorno (con valores por defecto):

| Variable | Por defecto |
|---|---|
| `INFLUXDB_ORG` | `deusto` |
| `INFLUXDB_TOKEN` | `udmt_super_secure_token` |
| `INFLUXDB_URL` | `http://db:8086` |

## Mosquitto

La configuración mínima en `mosquitto/config/mosquitto.conf` habilita acceso anónimo. El ESP32 envía credenciales (`admin`/`admin`) por compatibilidad, pero no son verificadas.

## Estructura de archivos

```
esp32-server/
├── compose.yaml              # Orquestación Docker Compose
├── mosquitto/
│   └── config/
│       └── mosquitto.conf    # Configuración del broker MQTT
├── server/
│   ├── Dockerfile
│   ├── requirements.txt      # paho-mqtt, influxdb-client
│   ├── server.py             # Punto de entrada: suscripción MQTT
│   └── db_manager.py         # Decodificación CAN + escritura InfluxDB
└── db/
    └── data/                 # Datos persistentes de InfluxDB (volumen)
```

## Relación con esp32-can-monitor

Este servidor recibe los mensajes publicados por el firmware del ESP32. Ver el repositorio [esp32-can-monitor](../esp32-can-monitor) para detalles del firmware y el formato binario de las tramas.
