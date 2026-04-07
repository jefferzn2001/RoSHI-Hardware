#include <ESP8266WiFi.h>
#include <espnow.h>
#include <Wire.h>
#include "SparkFun_BNO08x_Arduino_Library.h"

#define BNO_ADDR      0x4A
#define REPORT_US     10000      // 100 Hz
#define BAUDRATE      115200

const uint8_t TRACKER_ID = 9;    // set unique ID per node
uint8_t peerMAC[] = { 0x34, 0xCD, 0xB0, 0x34, 0x93, 0xE4 };

BNO08x imu;

/* ---- 40‑byte packet ---- */
typedef struct __attribute__((packed)) {
  uint8_t tracker_id;
  float   ax, ay, az;
  float   roll, pitch, yaw;
  float   qI, qJ, qK, qW;
  uint8_t battery_percent;
} IMUDataPacket;

IMUDataPacket pkt;

/* ---- battery helpers (factor 5.00) ---- */
const float ADC_TO_VBAT = 5.00f;

float rawToVoltage(uint16_t raw)
{
  return (raw / 1023.0f) * 1.0f * ADC_TO_VBAT;
}
uint8_t vToPercent(float v)
{
  v = constrain(v, 3.3f, 4.2f);
  return (uint8_t)(((v - 3.3f) / 0.9f) * 100.0f);
}

/* ---- setup ---- */
void setup() {
  Serial.begin(BAUDRATE);
  Wire.begin(); Wire.setClock(400000); delay(200);

  if (!imu.begin(BNO_ADDR, Wire)) { Serial.println("IMU fail"); while (1); }
  imu.enableRotationVector(REPORT_US);
  imu.enableAccelerometer(REPORT_US);

  WiFi.mode(WIFI_STA); WiFi.disconnect();
  if (esp_now_init() != 0) { Serial.println("ESP‑NOW fail"); while (1); }
  esp_now_set_self_role(ESP_NOW_ROLE_CONTROLLER);
  esp_now_add_peer(peerMAC, ESP_NOW_ROLE_SLAVE, 1, NULL, 0);

  Serial.println("Tracker: sending full quat + batt%");
}

/* ---- main loop ---- */
void loop() {
  if (!imu.getSensorEvent()) return;

  static float ax, ay, az, roll, pitch, yaw, qI, qJ, qK, qW;
  static uint8_t got = 0;

  switch (imu.getSensorEventID()) {
    case SENSOR_REPORTID_ROTATION_VECTOR:
      qI = imu.getQuatI(); qJ = imu.getQuatJ();
      qK = imu.getQuatK(); qW = imu.getQuatReal();
      roll  = imu.getRoll()  * 180.0f / PI;
      pitch = imu.getPitch() * 180.0f / PI;
      yaw   = imu.getYaw()   * 180.0f / PI;
      got |= 0b01; break;

    case SENSOR_REPORTID_ACCELEROMETER:
      ax = imu.getAccelX(); ay = imu.getAccelY(); az = imu.getAccelZ();
      got |= 0b10; break;
  }

  if (got == 0b11) {
    got = 0;

    uint16_t raw = analogRead(A0);
    float    v   = rawToVoltage(raw);
    uint8_t  batt= vToPercent(v);

    /* fill packet */
    pkt.tracker_id = TRACKER_ID;
    pkt.ax = ax; pkt.ay = ay; pkt.az = az;
    pkt.roll = roll; pkt.pitch = pitch; pkt.yaw = yaw;
    pkt.qI = qI; pkt.qJ = qJ; pkt.qK = qK; pkt.qW = qW;
    pkt.battery_percent = batt;

    esp_now_send(peerMAC, (uint8_t*)&pkt, sizeof(pkt));

    /* local debug (keeps raw for calibration) */
    Serial.printf("ID:%d raw:%u v:%.2f batt:%u%%\n",
                  TRACKER_ID, raw, v, batt);
  }
}


