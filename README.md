# 📌 Proyecto: Integración de ESP32, Mosquitto e InfluxDB

## 📝 Descripción
Este proyecto tiene como objetivo la integración de una **ESP32**, un **servidor Mosquitto (MQTT)** y **InfluxDB** para el almacenamiento y visualización de datos provenientes del **bus CAN de una moto eléctrica**.

La ESP32 actúa como **nodo de adquisición**, recibiendo tramas CAN de diferentes componentes, como la ECU y el BMS. Estas tramas se envían mediante **MQTT** a un servidor Mosquitto y posteriormente se almacenan en InfluxDB mediante un cliente Python. La información es procesada y organizada en **measurements** dentro de un **bucket** en InfluxDB.

Para la visualización de los datos, utilizamos **Grafana**, donde se diseñarán dashboards personalizados para analizar el estado del vehículo en tiempo real.

Este sistema permite un **monitoreo eficiente**, asegurando la persistencia y accesibilidad de los datos con una estructura optimizada para su análisis.

## 🚀 Planificación

### 1️⃣ Conexión y almacenamiento de datos
- Configurar la ESP32 para enviar datos a Mosquitto por WiFi.
- Configurar Mosquitto para que escuche en la interfaz `wlan`.
- Implementar el cliente de Python para almacenar datos en InfluxDB.
- Asegurar la persistencia y correcto almacenamiento de datos en la base de datos.

### 2️⃣ Extracción y procesamiento de tramas CAN
- Implementar `switch-case` para extraer información de las tramas.
- Validar el formato de las tramas para evitar errores en el almacenamiento.

📐 **Formato de la trama CAN almacenada en InfluxDB**:
```plaintext
ID (4 bytes)      TIMESTAMP (8 bytes)      PAYLOAD (8 bytes)
"0CF11E05"  +  "00000195e0fdc5ee"  +  "05000000C3010000"
```
- **ID**: Identifica el dispositivo y tipo de mensaje.
- **TIMESTAMP**: Reemplazado por el timestamp actual al insertarse en InfluxDB.
- **PAYLOAD**: Datos a procesar según el tipo de componente.

⚠️ **Cualquier error de formato hará que el mensaje sea descartado.**

## 🗄️ Base de datos
Usamos **InfluxDB** como base de datos NoSQL para almacenar tramas del protocolo CAN de la moto. Las tramas llegan por MQTT y se insertan mediante un cliente de Python.

📐 **Estructura del bucket `udmt` en InfluxDB:**
```plaintext
Bucket (udmt):
    ├── Measurement (ECU):
    │   ├── Point: Definir tramas de la ECU
    ├── Measurement (BMS):
    │   ├── Point: Definir tramas de la BMS
```
📌 **Ejemplo de `Point` en la medida `ECU`**:
```plaintext
Measurement: ECU
    ├── Point: rpm=3200, temperatura_motor=90, timestamp=1711190400000
    ├── Point: voltaje=395, corriente=52, estado=OK, timestamp=1711190410000
```

📍 **Recursos para la extracción de datos:**
- **ECU**: [Protocolo CAN de Kelly Controller](https://media.kellycontroller.com/new/Sinusoidal-Wave-Controller-KLS-D-8080I-8080IPS-Broadcast-CAN-Protocol.pdf)
- **BMS**: [Protocolo CAN de Daly](https://robu.in/wp-content/uploads/2021/10/Daly-CAN-Communications-Protocol-V1.0-1.pdf)
- **Ejemplo de trama ECU:**
```plaintext
2B 41 33 00 01 20 00 00
05 00 00 00 C3 01 00 00
```

## 📊 Visualización de datos con Grafana
Para visualizar los datos utilizaremos **Grafana**, implementado mediante **Docker Compose** para facilitar su configuración.

📌 **Pasos para la implementación:**
1. Descargar e instalar **Grafana** mediante Docker Compose.
2. Conectar Grafana con el contenedor de **InfluxDB v2**.
3. Diseñar un **dashboard** para la visualización de datos.

## ⚠️ Tareas pendientes
- Asegurar la conexión entre InfluxDB y Grafana.
- Elaborar el Dashboard en Grafana.
- Revisar el tiempo mínimo de vida de las tramas en InfluxDB, ya que si son un poco viejas, no las registra correctamente.

✏️ **Notas finales:**
- Se debe asegurar que InfluxDB y Mosquitto estén correctamente configurados para garantizar la persistencia y transmisión de los datos.
- La implementación de la interfaz puede ser opcional si Grafana cumple con las necesidades del proyecto.


