# 📌 Proyecto: Integración de ESP32, Mosquitto e InfluxDB

## 🚀 Planificación

### 1️⃣ Establecer conexión exitosa con Mosquitto por WiFi
- Configurar el cliente en la ESP32.
- Configurar Mosquitto para que escuche en la interfaz `wlan`.

### 2️⃣ Diseño de la base de datos
- Setup de InfluxDB.
- Asegurar la persistencia de los datos.
- Diseñar la estructura de la base de datos (tablas y campos) y documentarla.

### 3️⃣ Extracción de tramas
- Implementar `switch-case` para extraer información de las tramas.
- Almacenar todos los datos correctamente.

## 🔧 Posibles mejoras
- ✅ Conexión directa con el servidor mediante un punto de acceso.
- ✅ Interfaz para visualizar los datos (considerar Grafana u otro software para evitar diseñarla manualmente).

---

## 🗄️ Base de datos
Usaremos **InfluxDB** como base de datos NoSQL.

📌 **Conceptos clave:**
- No hay bases de datos tradicionales, sino **buckets**.
- Los **buckets** contienen **measurements** (medidas) con política de persistencia (datos eliminados después de cierto tiempo).
- Los **measurements** almacenan **points** con la siguiente estructura:
  - **Tags** (indexados).
  - **Fields** (valores numéricos no indexados).
  - **Timestamps** (marca de tiempo).

📊 **Visualización**: Los datos se analizarán y representarán con **Grafana** mediante dashboards personalizados.

---

## 📐 Diseño

📌 **Estructura del bucket** (`udmt`):

```plaintext
Bucket (udmt):
    ├── Measurement (ECU):
    │   ├── Point (definir todas las tramas que puede proporcionar la ECU)
    ├── Measurement (BMS):
    │   ├── Point (definir todas las tramas que puede proporcionar la BMS)
```

📌 **Ejemplo de `Point` en la medida `ECU`**:
```plaintext
Measurement: ECU
    ├── Point: rpm=3200, temperatura_motor=90, timestamp=1711190400000
    ├── Point: voltaje=395, corriente=52, estado=OK, timestamp=1711190410000
```

---

## 🔍 Recursos para la extracción de datos
- **ECU**: [Protocolo CAN de Kelly Controller](https://media.kellycontroller.com/new/Sinusoidal-Wave-Controller-KLS-D-8080I-8080IPS-Broadcast-CAN-Protocol.pdf)
- **BMS**: [Protocolo CAN de Daly](https://robu.in/wp-content/uploads/2021/10/Daly-CAN-Communications-Protocol-V1.0-1.pdf)

---

## 📊 Análisis de datos
1. Descargar e instalar **Grafana**.
2. Conectar Grafana con el contenedor de **InfluxDB v2**.
3. Extraer datos y diseñar un **dashboard** para visualización.

---

✏️ **Notas:**
- Se debe asegurar que InfluxDB y Mosquitto estén correctamente configurados para garantizar la persistencia y transmisión de los datos.
- La implementación de la interfaz puede ser opcional si Grafana cumple con las necesidades del proyecto.


