#include <Arduino.h>
#include <HardwareSerial.h>

#define PWM1 25
#define DIR1 26

char cmd = 0;

const int Cylinder_Bounce_ball = 5;
const int Cylinder_Receive = 18;
const int Cylinder_drawer = 19;

const int sensorTop = 34;
const int sensorBottom = 35;

const int pwmChannel1 = 0;
const int pwmFreq = 5000;
const int pwmResolution = 12;

HardwareSerial SerialUART(1);

bool movingUp = false;
bool movingDown = false;
bool allowUp = true;
bool allowDown = false;

bool passedBottom = false;
bool passedTop = false;

void stopMotor() {
  ledcWrite(pwmChannel1, 0);
  digitalWrite(DIR1, LOW);
  movingUp = false;
  movingDown = false;
  passedBottom = false;
  passedTop = false;
}

void setup() {
  Serial.begin(115200);
  SerialUART.begin(115200, SERIAL_8N1, -1, 17);
  ledcSetup(pwmChannel1, pwmFreq, pwmResolution);
  ledcAttachPin(PWM1, pwmChannel1);

  pinMode(DIR1, OUTPUT);
  pinMode(Cylinder_Bounce_ball, OUTPUT);
  pinMode(Cylinder_Receive, OUTPUT);
  pinMode(Cylinder_drawer, OUTPUT);
  pinMode(sensorTop, INPUT);
  pinMode(sensorBottom, INPUT);

  stopMotor();
  Serial.println("ESP32 พร้อมทำงาน");
}

void testrun() {
  if (movingUp) {
    if (digitalRead(sensorBottom) == HIGH) {
      passedBottom = true;
    }
    if (passedBottom && digitalRead(sensorBottom) == LOW) {
      Serial.println("⬆️ หยุดเมื่อเจอเซ็นเซอร์ล่าง");
      stopMotor();
      allowUp = false;
      allowDown = true;
    }
  }

  if (movingDown) {
    if (digitalRead(sensorTop) == HIGH) {
      passedTop = true;
    }
    if (passedTop && digitalRead(sensorTop) == LOW) {
      Serial.println("⬇️ หยุดเมื่อเจอเซ็นเซอร์บน");
      stopMotor();
      allowUp = true;
      allowDown = false;
    }
  }
}

void handleCommand(char cmd) {
  if (movingUp || movingDown) {
    Serial.println("⚠️ กำลังเคลื่อนที่อยู่ ไม่รับคำสั่งใหม่");
    return;
  }

  switch (cmd) {
    case 'k':
      if (allowUp) {
        Serial.println("▶️ เริ่มยกขึ้น");
        digitalWrite(DIR1, LOW);
        ledcWrite(pwmChannel1, 1800);
        movingUp = true;
      } else {
        Serial.println("❌ ไม่สามารถยกขึ้นได้");
      }
      break;

    case 'l':
      if (allowDown) {
        Serial.println("▶️ เริ่มดึงลง");
        digitalWrite(DIR1, HIGH);
        ledcWrite(pwmChannel1, 1000);
        movingDown = true;
      } else {
        Serial.println("❌ ไม่สามารถดึงลงได้");
      }
      break;

    case 'x':
      stopMotor();
      break;

    case 'b':
      digitalWrite(Cylinder_drawer, HIGH);
      delay(1500);
      digitalWrite(Cylinder_Bounce_ball, HIGH);
      digitalWrite(Cylinder_Receive, HIGH);
      delay(100);
      digitalWrite(Cylinder_Bounce_ball, LOW);
      delay(500);
      digitalWrite(Cylinder_Receive, LOW);
      delay(1500);
      digitalWrite(Cylinder_drawer, LOW);
      break;

    case 'M':
      digitalWrite(Cylinder_drawer, HIGH);
      break;

    case 'm':
      digitalWrite(Cylinder_drawer, LOW);
      break;

    case 'N':
      digitalWrite(Cylinder_Receive, HIGH);
      break;

    case 'n':
      digitalWrite(Cylinder_Receive, LOW);
      break;

    default:
      Serial.println("⚠️ คำสั่งไม่รู้จัก");
      break;
  }
}

void loop() {
  if (Serial.available()) {
    cmd = Serial.read();
    Serial.print("📥 รับคำสั่ง: ");
    Serial.println(cmd);
    SerialUART.write(cmd);
    handleCommand(cmd);
  }

  testrun();
}
