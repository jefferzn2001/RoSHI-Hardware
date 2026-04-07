import serial
import serial.tools.list_ports
import re
import time
import os
import numpy as np
import threading

class IMUReader:
    def __init__(self, baudrate=115200, port=None):
        self.baudrate = baudrate
        self.ser = None
        self.connected_imus = {}  # IMU ID -> battery level (IMUs only)
        self.latest_data = {}     # IMU ID -> full data
        self._imu_last_ms = {}    # IMU ID -> last received time (monotonic seconds)
        self.button_state = None  # dict: {"id":0, "btn14":0/1, "btn12":0/1}
        self._button_last_ms = None
        self._running = False
        self._connect(port)
        self._compile_patterns()
        self._start_background_thread()
        self._wait_for_data()
        
    def _compile_patterns(self):
        self.re_imu = re.compile(
            r"ID:(\d+) \| r:([-\d.]+) p:([-\d.]+) y:([-\d.]+) \| "
            r"ax:([-\d.]+) ay:([-\d.]+) az:([-\d.]+) \| "
            r"qI:([-\d.]+) qJ:([-\d.]+) qK:([-\d.]+) qW:([-\d.]+) \| "
            r"batt:(\d+)%"
        )
        self.re_btn = re.compile(
            r"BTN ID:(\d+) \| (?:batt:(\d+)% \| )?BTN14:(\d+) BTN12:(\d+)"
        )
    
    def _connect(self, port=None):
        try:
            if port and self._try_port(port):
                return True
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                if 'usb' in p.device.lower() and self._try_port(p.device):
                    return True
            print("No ESP32 host found!")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
            
    def _try_port(self, port):
        try:
            self.ser = serial.Serial(port, self.baudrate, timeout=0.1)
            time.sleep(0.1)
            return True
        except:
            return False

    def _wait_for_data(self, timeout=1.0):
        print("Waiting for IMU data", end="", flush=True)
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.latest_data or self.button_state is not None:
                print(" - Connected!")
                return True
            print(".", end="", flush=True)
            time.sleep(0.1)
        print(" - No IMUs found!")
        return False

    def _map_button_state(self, timeout_s: float = 0.8) -> int:
        if self.button_state is None or self._button_last_ms is None:
            return 0
        if (time.time() - self._button_last_ms) > timeout_s:
            return 0
        if self.button_state.get("btn14", 0):
            return 1
        if self.button_state.get("btn12", 0):
            return 2
        return 0

    def _background_read(self):
        while self._running:
            try:
                if self.ser and self.ser.in_waiting:
                    line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        time.sleep(0.001)
                        continue
                    # IMU
                    m = self.re_imu.match(line)
                    if m:
                        (imu_id, roll, pitch, yaw,
                         ax, ay, az,
                         qI, qJ, qK, qW,
                         battery) = m.groups()
                        imu_id = int(imu_id)
                        battery = int(battery)
                        self.connected_imus[imu_id] = battery
                        self.latest_data[imu_id] = {
                            "euler": {"roll": float(roll), "pitch": float(pitch), "yaw": float(yaw)},
                            "accel": {"x": float(ax), "y": float(ay), "z": float(az)},
                            "quaternion": {"i": float(qI), "j": float(qJ), "k": float(qK), "w": float(qW)},
                            "battery": battery
                        }
                        self._imu_last_ms[imu_id] = time.time()
                        continue
                    # Button (including host timeout BTN14:0 BTN12:0 lines)
                    b = self.re_btn.match(line)
                    if b:
                        (bid, batt, b14, b12) = b.groups()
                        self.button_state = {
                            "id": int(bid),
                            "btn14": int(b14),
                            "btn12": int(b12)
                        }
                        self._button_last_ms = time.time()
                        continue
                # If no serial line arrived, still allow timeout to 0 by not changing _button_last_ms
            except Exception:
                pass
            time.sleep(0.001)

    def _start_background_thread(self):
        self._running = True
        self.read_thread = threading.Thread(target=self._background_read, daemon=True)
        self.read_thread.start()
            
    def _fresh_imus(self, timeout_s: float = 0.05):
        now = time.time()
        fresh_ids = []
        for imu_id, ts in list(self._imu_last_ms.items()):
            if (now - ts) <= timeout_s:
                fresh_ids.append(imu_id)
        return sorted(fresh_ids)

    def list(self):
        printed = False
        fresh = self._fresh_imus()
        if fresh:
            print("\nConnected IMUs:")
            for imu_id in fresh:
                batt = self.connected_imus.get(imu_id)
                if batt is not None:
                    print(f"IMU #{imu_id:2d}: {batt:3d}% battery")
            printed = True
        mapped = self._map_button_state()
        if self.button_state is not None or mapped != 0:
            if printed:
                print("")
            print(f"Buttons (ID:0): state={mapped}")
            printed = True
        if not printed:
            print("No devices detected")
        
    def read(self):
        ordered = {}
        # Only include fresh IMUs
        for imu_id in self._fresh_imus():
            if imu_id in self.latest_data:
                ordered[imu_id] = self.latest_data[imu_id]
        mapped = self._map_button_state()
        if self.button_state is not None or mapped != 0:
            ordered[0] = {"button_state": mapped}
        return ordered
        
    def button_state_only(self):
        return {"state": self._map_button_state()}
        
    def stream(self):
        try:
            print("\nStreaming IMU data... Press Ctrl+C to exit\n")
            while True:
                # Filter to fresh IMUs to avoid stale printing
                fresh_ids = self._fresh_imus()
                data = {imu_id: self.latest_data[imu_id] for imu_id in fresh_ids if imu_id in self.latest_data}
                os.system('cls' if os.name == 'nt' else 'clear')
                mapped = self._map_button_state()
                print(f"Buttons: state={mapped}\n")
                if data:
                    print("Connected IMUs:\n")
                    for imu_id in sorted(data.keys()):
                        imu_data = data[imu_id]
                        print(f"IMU #{imu_id}")
                        print("Euler angles:")
                        print(f"  Roll : {imu_data['euler']['roll']:7.2f}°")
                        print(f"  Pitch: {imu_data['euler']['pitch']:7.2f}°")
                        print(f"  Yaw  : {imu_data['euler']['yaw']:7.2f}°")
                        print("Acceleration:")
                        print(f"  X: {imu_data['accel']['x']:7.3f}")
                        print(f"  Y: {imu_data['accel']['y']:7.3f}")
                        print(f"  Z: {imu_data['accel']['z']:7.3f}")
                        q = imu_data['quaternion']
                        print("Quaternion:")
                        print(f"  W: {q['w']:7.3f}")
                        print(f"  I: {q['i']:7.3f}")
                        print(f"  J: {q['j']:7.3f}")
                        print(f"  K: {q['k']:7.3f}\n")
                else:
                    print("Waiting for IMU data...")
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\nStopped streaming.")
            
    def close(self):
        self._running = False
        if self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        if self.ser and self.ser.is_open:
            self.ser.close()
