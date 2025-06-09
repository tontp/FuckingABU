#include <Arduino.h>
#include <HardwareSerial.h>

#define ENA 25  // PWM control pin
#define IN1 26  // Direction control
#define IN2 27  // Direction control

const int pwmChannel = 0;     // ช่อง PWM สำหรับ ENA
const int pwmFreq = 5000;     // ความถี่ 5kHz
const int pwmResolution = 8;  // ความละเอียด 8 บิต (0-255)

HardwareSerial SerialUART(1);  // UART1

void setup() {
  Serial.begin(115200);

  // ตั้งค่า PWM ด้วย ledc
  ledcSetup(pwmChannel, pwmFreq, pwmResolution);
  ledcAttachPin(ENA, pwmChannel);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  stopMotor();
}

void loop() {
  runMotorBackward();
  Serial.println("B");
  delay(5000);

  runMotorForward();
  Serial.println("F");
  delay(5000);

  if (Serial.available()) {
    char cmd = Serial.read();
    Serial.print("รับคำสั่งจากคอม: ");
    Serial.println(cmd);
    SerialUART.write(cmd);  // ส่งผ่าน UART ไปยัง ESP32 ตัวที่ 2

    if (cmd == 'J') {
      runMotorForward();
    } else if (cmd == 'L') {
      runMotorBackward();
    } else {
      stopMotor();
    }
  }
}

void runMotorForward() {
  ledcWrite(pwmChannel, 100);  // 0–255
  ledcWrite(IN1, 255);
  ledcWrite(IN2, 0);
}

void runMotorBackward() {
  ledcWrite(pwmChannel, 100);  // 0–255
  ledcWrite(IN1, 0);
  ledcWrite(IN2, 255);
}

void stopMotor() {
  ledcWrite(pwmChannel, 1);  // ปิด PWM
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}