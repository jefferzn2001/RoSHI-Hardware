# RoSHI Hardware

![RoSHI IMU tracker — exploded view](Images/IMUARIA.png)

This repository contains the **3D-printed parts** for the RoSHI paper, along with firmware and helper scripts in the layout below.

## Repository layout

| Path | Contents |
|------|----------|
| `3D Prints/` | STEP and STL models (receiver, IMU case, holder, and related parts) |
| `Firmware/IMU_Tracker/` | Tracker firmware (ESP8266 + BNO08x, ESP-NOW) |
| `Firmware/IMU_Receiver/HostRead/` | Host/receiver firmware (ESP32 + OLED) |
| `Firmware/python/` | `imu_reader.py`, `sample.py`, `visualize.py` — serial reader and examples |
| `Images/` | Figures such as the hardware render above |

## Python scripts

The scripts in `Firmware/python/` use only a few lightweight packages. Install them with:

```bash
pip install pyserial numpy matplotlib
```

From `Firmware/python/`, run e.g. `python sample.py` or `python visualize.py` with the ESP32 host connected over USB.
