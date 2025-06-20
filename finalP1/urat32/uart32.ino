#include <Arduino.h>
#include <HardwareSerial.h>

#define PWM1 25
#define DIR1 26

char cmdBuffer[10];  // buffer เก็บคำสั่ง
int cmdCount = 0;

const int Cylinder_Bounce_ball = 5;
const int Cylinder_Receive = 18;
const int Cylinder_drawer = 19;

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

// สำหรับ state ยิงบอลแบบ non-blocking
enum BounceBallState { IDLE, DRAWER_ON, BOUNCE_ON, BOUNCE_OFF, FINISHED };
BounceBallState bounceState = IDLE;
unsigned long bounceMillis = 0;

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

  stopMotor();
  Serial.println("ESP32 พร้อมทำงาน");
}

// ฟังก์ชันที่ทำงานยิงบอลแบบ non-blocking
void updateBounceBall() {
  unsigned long now = millis();

  switch (bounceState) {
    case IDLE:
      // ไม่ทำอะไร
      break;

    case DRAWER_ON:
      digitalWrite(Cylinder_drawer, HIGH);
      bounceMillis = now;
      bounceState = BOUNCE_ON;
      break;

    case BOUNCE_ON:
      if (now - bounceMillis >= 1500) {
        digitalWrite(Cylinder_Bounce_ball, HIGH);
        digitalWrite(Cylinder_Receive, HIGH);
        bounceMillis = now;
        bounceState = BOUNCE_OFF;
      }
      break;

    case BOUNCE_OFF:
      if (now - bounceMillis >= 100) {
        digitalWrite(Cylinder_Bounce_ball, LOW);
        bounceMillis = now;
        bounceState = FINISHED;
      }
      break;

    case FINISHED:
      if (now - bounceMillis >= 500) {
        digitalWrite(Cylinder_Receive, LOW);
        bounceMillis = now;
        bounceState = (BounceBallState)100; // สถานะพักรอปิดลิ้นชัก
      }
      break;

    case (BounceBallState)100:
      if (now - bounceMillis >= 1000) {
        digitalWrite(Cylinder_drawer, LOW);
        bounceState = IDLE;
        Serial.println("⚡ ยิงลูกบอลเสร็จแล้ว");
      }
      break;
  }
}

void handleCommand(char c) {
  if ((movingUp || movingDown) && (c == 'k' || c == 'l')) {
    Serial.println("⚠️ กำลังเคลื่อนที่อยู่ ไม่รับคำสั่งขึ้นหรือลง");
    return;
  }

  switch (c) {

    case 'x':
      stopMotor();
      break;

    case 'b':
      if (bounceState == IDLE) {
        bounceState = DRAWER_ON;
        Serial.println("▶️ เริ่มยิงลูกบอล");
      } else {
        Serial.println("⚠️ กำลังยิงลูกบอลอยู่");
      }
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
  // อ่านคำสั่งหลายตัวถ้าเข้ามาพร้อมกัน (multi-command)
  while (Serial.available()) {
    char c = Serial.read();
    Serial.print("📥 รับคำสั่ง: ");
    Serial.println(c);
    SerialUART.write(c);
    handleCommand(c);
  }

  // อัปเดตสถานะยิงบอลแบบ non-blocking
  updateBounceBall();
}
