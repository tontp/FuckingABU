#include <Arduino.h>
#include <HardwareSerial.h>

#define PWM1 25
#define DIR1 26

char cmd = 0;

const int Cylinder_Bounce_ball = 5;  // relay ch4
const int Cylinder_Receive = 18;     // relay ch5
const int Cylinder_drawer = 19;      // relay ch6

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

void stopMotor() {
  ledcWrite(pwmChannel1, 0);
  digitalWrite(DIR1, LOW);
  movingUp = false;
  movingDown = false;
}

void setup() {
  Serial.begin(115200);
  SerialUART.begin(115200, SERIAL_8N1, -1, 17);

  Serial.println("ESP32 ตัวที่ 1 พร้อมส่งข้อมูลผ่าน UART");

  ledcSetup(pwmChannel1, pwmFreq, pwmResolution);
  ledcAttachPin(PWM1, pwmChannel1);

  pinMode(DIR1, OUTPUT);
  pinMode(Cylinder_Bounce_ball, OUTPUT);
  pinMode(Cylinder_Receive, OUTPUT);
  pinMode(Cylinder_drawer, OUTPUT);

  pinMode(sensorTop, INPUT);
  pinMode(sensorBottom, INPUT);

  stopMotor();
}

void testrun() {
  if (movingUp && digitalRead(sensorBottom) == LOW) {
    Serial.println("⬆️ ตอนขึ้น: เจอเซ็นเซอร์ล่าง -> หยุด");
    stopMotor();
    allowUp = false;
    allowDown = true;
  }

  if (movingDown && digitalRead(sensorTop) == LOW) {
    Serial.println("⬇️ ตอนลง: เจอเซ็นเซอร์บน -> หยุด");
    stopMotor();
    allowUp = true;
    allowDown = false;
  }
}

void handleCommand(char cmd) {
  switch (cmd) {
    case 'k':  // ยกขึ้น
      if (allowUp && !movingUp && !movingDown) {
        Serial.println("▶️ เริ่มยกขึ้น");
        digitalWrite(DIR1, LOW);
        ledcWrite(pwmChannel1, 1800);
        movingUp = true;
      } else {
        Serial.println("❌ ไม่สามารถยกขึ้นได้");
      }
      break;

    case 'l':  // ดึงลง
      if (allowDown && !movingUp && !movingDown) {
        Serial.println("▶️ เริ่มยกลง");
        digitalWrite(DIR1, HIGH);
        ledcWrite(pwmChannel1, 1000);
        movingDown = true;
      } else {
        Serial.println("❌ ไม่สามารถยกลงได้");
      }
      break;

    case 'x':
      stopMotor();
      allowUp = true;
      allowDown = false;
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
      delay(3000);
      digitalWrite(Cylinder_Receive, HIGH);
      break;

    case 'm':
      digitalWrite(Cylinder_Receive, LOW);
      delay(3000);
      digitalWrite(Cylinder_drawer, LOW);
      break;

    case 'N':
      digitalWrite(Cylinder_Receive, HIGH);
      break;

    case 'n':
      digitalWrite(Cylinder_Receive, LOW);
      break;

    default:
      Serial.println("คำสั่งไม่รู้จัก");
      break;
  }
}

void loop() {
  if (Serial.available()) {
    cmd = Serial.read();
    Serial.print("📥 รับคำสั่งจากคอม: ");
    Serial.println(cmd);
    SerialUART.write(cmd);
    handleCommand(cmd);
  }

  testrun();  // ตรวจสอบเซ็นเซอร์เสมอเพื่อหยุดมอเตอร์
}
