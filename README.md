# RoSHI Hardware

![RoSHI IMU tracker — exploded view](Images/IMUARIA.png)

Wireless IMU motion tracking for RoSHI: body-worn trackers stream orientation and acceleration to a host over **ESP-NOW**, with **Python** utilities for logging and visualization. Enclosure parts are provided as **STEP** files for 3D printing.

## Contents

| Area | Description |
|------|-------------|
| **Firmware** | `IMU_Tracker` — ESP8266 + BNO08x, sends fused pose and battery %; `IMU_Receiver/HostRead` — ESP32 host with OLED status grid |
| **Python** | `imu_reader.py` — serial reader for host output; `sample.py` / `visualize.py` — examples |
| **3D Prints** | Receiver base/cap, IMU case, and holder components (`*.STEP`) |

## Quick start (Python)

1. Flash the host firmware and connect the ESP32 over USB.
2. Install dependencies (e.g. `pyserial`, `numpy` as used by the scripts).
3. From `Firmware/python`, run `sample.py` or `visualize.py` as needed.

Tracker and host **IDs, MAC addresses, and WiFi roles** are set in the Arduino sources—adjust before deploying multiple nodes.

## License

Add a license file if you want to specify terms for hardware designs and firmware.
