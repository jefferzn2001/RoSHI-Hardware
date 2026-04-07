from imu_reader import IMUReader

# Create IMU reader (automatically starts reading in background)
imu = IMUReader()

# List connected IMUs and current button state (if any)
imu.list()

# Get latest data (includes tracker 0 for buttons if present)
# data = imu.read()
# print("\nLatest data:", data)

# Read button via helper
# btn = imu.button_state_only()
# print("\nButton state (helper):", btn if btn is not None else "No button state yet")


# stream continuously (shows buttons and IMUs live)
imu.stream()
 
