# esp32-server

Servidor de preparacion para la telemetria CAN de Deusto Moto Team / MotoStudent Electric.

El stack actual recibe mensajes publicados por una ESP32 mediante MQTT, procesa tramas CAN en Python y guarda los datos en InfluxDB. Este repositorio todavia esta en fase base: el objetivo es ir hacia una ingesta CAN robusta, simulacion, tests y dashboards, manteniendo cambios pequenos y revisables.

> Este proyecto no debe considerarse todavia telemetria en vivo lista para uso en pista.

## Arquitectura actual

El entorno se levanta con Docker Compose y contiene tres servicios:

| Servicio | Funcion |
| --- | --- |
| `mosquitto` | Broker MQTT que recibe mensajes desde la ESP32. |
| `esp32-server` | Servicio Python que se suscribe al topic MQTT y pasa payloads CAN a `DBManager`. |
| `db` | InfluxDB 2.x para almacenar datos de series temporales. |

Flujo esperado:

```text
ESP32 firmware
  -> MQTT topic test_topic
  -> Mosquitto
  -> esp32-server Python
  -> InfluxDB bucket
```

## Estructura

```text
esp32-server/
|-- AGENTS.md
|-- README.md
|-- compose.yaml
|-- .env.example
|-- mosquitto/
|   `-- config/
|       `-- mosquitto.conf
`-- server/
    |-- Dockerfile
    |-- requirements.txt
    |-- server.py
    `-- db_manager.py
```

## Requisitos

- Docker
- Docker Compose
- Python 3, solo para comprobaciones locales opcionales

## Configuracion

1. Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

En PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Edita `.env` y cambia los placeholders locales:

```dotenv
INFLUXDB_PASSWORD=change-me-local-password
INFLUXDB_TOKEN=change-me-local-token
```

No subas `.env` al repositorio. El archivo `.env.example` solo contiene valores de ejemplo.

Variables principales:

| Variable | Uso |
| --- | --- |
| `MOSQUITTO_EXTERNAL_PORT` | Puerto expuesto en la maquina host para MQTT. |
| `MOSQUITTO_INTERNAL_PORT` | Puerto interno del contenedor Mosquitto. |
| `INFLUXDB_EXTERNAL_PORT` | Puerto expuesto para la UI/API de InfluxDB. |
| `INFLUXDB_INTERNAL_PORT` | Puerto interno del contenedor InfluxDB. |
| `INFLUXDB_USERNAME` | Usuario inicial de InfluxDB. |
| `INFLUXDB_PASSWORD` | Password inicial de InfluxDB. |
| `INFLUXDB_ORG` | Organizacion de InfluxDB. |
| `INFLUXDB_BUCKET` | Bucket usado por InfluxDB y el servidor Python. |
| `INFLUXDB_TOKEN` | Token local para escribir en InfluxDB. |
| `INFLUXDB_URL` | URL que usa el servidor Python para conectar con InfluxDB. |
| `MQTT_HOST` | Broker MQTT usado por el servidor Python. Por defecto, `mosquitto` dentro de Docker. |
| `MQTT_PORT` | Puerto MQTT usado por el servidor Python. Por defecto, `1883`. |
| `MQTT_TOPIC` | Topic al que se suscribe el servidor Python. Por defecto, `test_topic`. |
| `MQTT_CLIENT_ID` | Client ID MQTT opcional para el servidor Python. |

## Puesta en marcha

Con `.env` creado:

```bash
docker compose up --build
```

Servicios expuestos por defecto:

| Servicio | URL/Puerto |
| --- | --- |
| Mosquitto | `localhost:2000` |
| InfluxDB | `http://localhost:8086` |

El servicio Python se ejecuta dentro de Docker con:

```bash
python3 -u server.py
```

## Formato de mensajes esperado

El servidor espera strings hexadecimales de 40 caracteres, equivalentes a 20 bytes:

```text
Bytes  0-3   CAN ID      uint32 big-endian
Bytes  4-11  timestamp   uint64 big-endian, ms desde arranque ESP32
Bytes 12-19  payload CAN 8 bytes
```

El topic MQTT usado por defecto por `server.py` es `test_topic`. Si cambias `MQTT_TOPIC`, usa el mismo topic al ejecutar el simulador MQTT/CAN.

## Comprobaciones basicas

Validar sintaxis Python:

```bash
python -m py_compile server/server.py server/db_manager.py
```

Validar la configuracion de Compose, con `.env` presente:

```bash
docker compose config
```

Levantar el stack:

```bash
docker compose up --build
```

Ejecutar una prueba end-to-end local sin ESP32:

```powershell
py tools\publish_mqtt_frames.py --host localhost --port 2000 --topic test_topic --count 5
```

Ver la guia completa en [docs/e2e-smoke-test.md](docs/e2e-smoke-test.md).

## Estado actual y siguientes pasos

Estado actual:

- MQTT conectado mediante Mosquitto.
- Decodificacion CAN basica en `server/db_manager.py`.
- Escritura en InfluxDB mediante `influxdb-client`.
- Configuracion local externalizada a `.env`.

Trabajo pendiente recomendado:

- Anadir tests unitarios para decodificacion CAN.
- Anadir simulador local de mensajes MQTT/CAN.
- Definir convenciones de measurements, tags y campos en InfluxDB.
- Preparar dashboards una vez estabilizado el modelo de datos.
- Revisar configuracion MQTT para entornos no locales.
