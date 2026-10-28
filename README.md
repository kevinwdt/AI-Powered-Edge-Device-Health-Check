# AI-Powered Edge Device Health Check

An AI-assisted monitoring prototype for edge devices and PLC-related gateways. It collects device telemetry over MQTT, evaluates operating health using a trained machine-learning model, stores observations in SQLite, and presents results through a Flask web dashboard.

## Overview

The project helps make edge-device health easier to inspect by combining incoming diagnostic data with three health classifications:

- **Healthy** — metrics are within expected operating ranges.
- **Warning** — elevated usage or potentially concerning conditions.
- **Critical** — severe operating conditions or out-of-range sensor readings.

The classifier uses a **Random Forest** trained on generated, labeled telemetry examples. Alongside each classification, rule-based logic provides a human-readable reason. This is a prototype: predictions should not be treated as a validated industrial safety system.

## Features

- **MQTT telemetry ingestion:** subscribes to device diagnostic topics and parses JSON payloads.
- **Health classification:** evaluates used memory, used storage, CPU usage and temperature.
- **Explainable status messages:** reports a plain-language reason for notable metrics.
- **SQLite history:** stores raw messages, derived metrics, predictions and timestamps.
- **Web dashboard:** displays latest device health and historical readings.
- **Device publishers:** includes a Raspberry Pi publisher and a simulated telemetry generator.
- **Local model training:** generates synthetic examples and saves the trained model as `model.pkl`.

## Technology Stack

| Component | Technology |
| --- | --- |
| Language | Python |
| Machine learning | scikit-learn, NumPy |
| Messaging | MQTT, paho-mqtt |
| Backend and dashboard | Flask, Bootstrap, JavaScript |
| Storage | SQLite |
| Device telemetry | Raspberry Pi / Linux and synthetic publishers |

## System Architecture

```text
Raspberry Pi / Simulated Device
              |
         MQTT telemetry
              |
          MQTT Broker
              |
      Python MQTT Subscriber
              |
       Feature Extraction
        /             \
   Random Forest    SQLite Database
   Health Status          |
        |                 |
        +-------+---------+
                |
          Flask Dashboard
```

The MQTT subscriber extracts `used_memory = totalmemory - remainingmemory` and `used_storage = storagetotal - remainingstorage`, then records incoming readings and an AI classification when a trained model is available.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/kevinwdt/AI-Powered-Edge-Device-Health-Check.git
cd AI-Powered-Edge-Device-Health-Check/"PLC AI project Capstone"/AI_v1
```

### 2. Set up Python

Python **3.10+** is recommended for the type annotations used in the code. Create and activate a virtual environment:

```bash
python -m venv .venv
```

On macOS / Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```bash
python -m pip install numpy scikit-learn flask paho-mqtt
```

### 3. Train the AI model

```bash
python train_ai_model.py
```

This generates synthetic training samples, trains a Random Forest classifier, prints evaluation results and creates a local `model.pkl` file.

**Note:** Model accuracy reported here reflects evaluation on synthetic data, not proven real-world diagnostic accuracy.

### 4. Start the application

```bash
python main.py
```

By default, the application:

- Connects to the public MQTT broker `test.mosquitto.org:1883`.
- Subscribes to `plc/devices/diagnostic/#`.
- Creates or opens `plc_health.db`.
- Runs the Flask dashboard at **http://127.0.0.1:5000**.

You can change the broker, topic or dashboard host/port in `main.py`.

### 5. Publish telemetry

For development without physical hardware, start a second terminal in the same directory and run:

```bash
python simulate_publisher.py
```

For a Raspberry Pi / Linux device, inspect the available publisher options:

```bash
python pi_publisher.py --help
```

Configure the publisher to use the **same broker** and a topic under `plc/devices/diagnostic/` as the subscriber.

## Example Device Telemetry

The MQTT subscriber supports JSON messages containing fields such as:

```json
{
  "time": 1730000000,
  "gateway": "edge-gateway-01",
  "siteid": "device-01",
  "totalmemory": 1873.92,
  "remainingmemory": 750.0,
  "storagetotal": 4249.6,
  "remainingstorage": 600.0,
  "cpuusage": 45.0,
  "temperature": 42.0
}
```

The system derives used memory and storage before passing the features to the classifier. Timestamps should be Unix epoch seconds.

## Project Structure

```text
AI-Powered-Edge-Device-Health-Check/
├── README.md
└── PLC AI project Capstone/
    └── AI_v1/
        ├── main.py                # Starts the services
        ├── base_Service.py        # Service lifecycle base class
        ├── mqtt_Client.py         # MQTT subscriber and feature extraction
        ├── ai_Model.py            # Model training, inference and explanations
        ├── train_ai_model.py      # Synthetic dataset generation and training
        ├── database_Access.py     # SQLite storage and queries
        ├── web_Server.py          # Flask dashboard
        ├── pi_publisher.py        # Raspberry Pi / Linux telemetry publisher
        ├── simulate_publisher.py  # Synthetic device telemetry publisher
        ├── plot_diagnostics.py    # Diagnostic plotting utility
        ├── test_ai_model.py       # Manual AI inference checks
        └── server.py              # Earlier service test / prototype
```

## Testing

After training, run the included inference checks:

```bash
python test_ai_model.py
```

These are basic manual test cases; the repository does not currently include a full automated test suite.

## Development Notes

- The system currently uses an **unencrypted public MQTT broker** by default. Do not publish sensitive or production device information to it.
- `model.pkl` is generated locally; train the model before expecting AI classifications.
- Classification and explanations use different mechanisms: the model predicts a category, while threshold-based rules generate the reason.
- For production use, consider secure MQTT transport, broker authentication, measured real-world model performance, more comprehensive tests and deployment hardening.

## Author

Maintained by [kevinwdt](https://github.com/kevinwdt).
