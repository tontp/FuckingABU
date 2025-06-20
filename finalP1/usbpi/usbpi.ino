#include <Arduino.h>

// มอเตอร์เดิน MDD10A
const int motorPWMPins[] = { 4, 14, 18, 17 };
const int motorDIRPins[] = { 15, 12, 19, 5 };

// ชุดยิง Cytron 20A
const int cytronPWM1 = 21;
const int cytronDIR1 = 22;
const int cytronPWM2 = 23;
const int cytronDIR2 = 2;

// รีเลย์
const int linear_UP = 32;
const int linear_DOWN = 33;
const int Cylinder_PUSH = 25;

const int MAX_DUTY = 4095;
HardwareSerial UART_IN(1);

String cmdBuffer = "";

bool moveCmdActive = false;
char moveCmd = 'x';

bool shooting = false;
unsigned long shootStartTime = 0;
const unsigned long shootDuration = 800;
int shootingLevel = 0;

bool liftUp = false;
bool liftDown = false;

float baseSpeed = 1.0;

void setup() {
  Serial.begin(115200);
  UART_IN.begin(115200, SERIAL_8N1, 16, -1);

  for (int i = 0; i < 4; i++) {
    pinMode(motorDIRPins[i], OUTPUT);
    ledcSetup(i, 5000, 12);
    ledcAttachPin(motorPWMPins[i], i);
    ledcWrite(i, 0);
  }

  // Cytron PWM
  ledcSetup(4, 5000, 12);
  ledcAttachPin(cytronPWM1, 4);
  ledcSetup(5, 5000, 12);
  ledcAttachPin(cytronPWM2, 5);
  pinMode(cytronDIR1, OUTPUT);
  pinMode(cytronDIR2, OUTPUT);

  // รีเลย์
  pinMode(linear_UP, OUTPUT);
  pinMode(linear_DOWN, OUTPUT);
  pinMode(Cylinder_PUSH, OUTPUT);

  Serial.println("✅ ESP32 พร้อมทำงานแบบ Multi-command State Machine");
}

void driveMotor(int dirPin, int pwmChannel, float power) {
  if (abs(power) < 0.01f) {
    digitalWrite(dirPin, LOW);
    ledcWrite(pwmChannel, 0);
    return;
  }
  digitalWrite(dirPin, power > 0 ? HIGH : LOW);
  ledcWrite(pwmChannel, int(abs(power) * MAX_DUTY));
}

void stopAllMotors() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(motorDIRPins[i], LOW);
    ledcWrite(i, 0);
  }
}

void updateShooterPower() {
  int duty = (shootingLevel * MAX_DUTY) / 3;
  ledcWrite(4, duty);
  ledcWrite(5, duty);
  digitalWrite(cytronDIR1, HIGH);
  digitalWrite(cytronDIR2, HIGH);
  Serial.printf("⚙️ ปรับระดับยิง = %d → duty=%d\n", shootingLevel, duty);
}

void shootBall() {
  if (!shooting) {
    digitalWrite(Cylinder_PUSH, HIGH);
    shootStartTime = millis();
    shooting = true;
    Serial.println("🔫 ยิงลูกบอล...");
  }
}

void updateLiftState() {
  digitalWrite(linear_UP, liftUp ? HIGH : LOW);
  digitalWrite(linear_DOWN, liftDown ? HIGH : LOW);
}

void processMoveCommand(char c) {
  float speed = baseSpeed;
  float m[4] = { 0, 0, 0, 0 };

  switch (c) {
    case 'w':
      m[1] = speed;
      m[3] = -speed;
      break;
    case 's':
      m[1] = -speed;
      m[3] = speed;
      break;
    case 'a':
      m[0] = speed;
      m[2] = -speed;
      break;
    case 'd':
      m[0] = -speed;
      m[2] = speed;
      break;
    case 'q':
      m[0] = speed;
      m[1] = speed;
      m[2] = speed;
      m[3] = speed;
      break;
    case 'e':
      m[0] = -speed;
      m[1] = -speed;
      m[2] = -speed;
      m[3] = -speed;
      break;
    case '6':
      m[0] = speed;
      m[1] = speed;
      m[2] = -speed;
      m[3] = -speed;
      break;
    case '7':
      m[0] = -speed;
      m[1] = speed;
      m[2] = speed;
      m[3] = -speed;
      break;
    case '8':
      m[0] = speed;
      m[1] = -speed;
      m[2] = -speed;
      m[3] = speed;
      break;
    case '9':
      m[0] = -speed;
      m[1] = -speed;
      m[2] = speed;
      m[3] = speed;
      break;
    default:
      // no movement
      break;
  }
  for (int i = 0; i < 4; i++) {
    driveMotor(motorDIRPins[i], i, m[i]);
  }
}

void loop() {
  while (UART_IN.available()) {
    char c = UART_IN.read();
    if (c != '\n' && c != '\r') {
      cmdBuffer += c;
    }
  }

  if (cmdBuffer.length() > 0) {
    // reset movement vectors
    float m[4] = { 0, 0, 0, 0 };
    liftUp = false;
    liftDown = false;
    bool shootCmd = false;
    bool stopShootingCmd = false;

    for (unsigned int i = 0; i < cmdBuffer.length(); i++) {
      char c = cmdBuffer[i];
      float speed = baseSpeed;

      switch (c) {
        case 'w':
          m[1] += speed;
          m[3] -= speed;
          break;
        case 's':
          m[1] -= speed;
          m[3] += speed;
          break;
        case 'a':
          m[0] += speed;
          m[2] -= speed;
          break;
        case 'd':
          m[0] -= speed;
          m[2] += speed;
          break;
        case 'q':  // หมุนซ้าย
          m[0] += speed;
          m[1] += speed;
          m[2] += speed;
          m[3] += speed;
          break;
        case 'e':  // หมุนขวา
          m[0] -= speed;
          m[1] -= speed;
          m[2] -= speed;
          m[3] -= speed;
          break;
        case '6':
          m[0] = speed;
          m[1] = speed;
          m[2] = -speed;
          m[3] = -speed;
          break;
        case '7':
          m[0] = -speed;
          m[1] = speed;
          m[2] = speed;
          m[3] = -speed;
          break;
        case '8':
          m[0] = speed;
          m[1] = -speed;
          m[2] = -speed;
          m[3] = speed;
          break;
        case '9':
          m[0] = -speed;
          m[1] = -speed;
          m[2] = speed;
          m[3] = speed;
          break;
        case 'x':
          for (int j = 0; j < 4; j++) m[j] = 0;
          shooting = false;
          digitalWrite(Cylinder_PUSH, LOW);
          stopAllMotors();
          break;
        case ' ': shootCmd = true; break;
        case 'z':
          stopShootingCmd = true;
          shootingLevel = 0;
          break;
        case '0':
        case '1':
        case '2':
        case '3':
          shootingLevel = c - '0';
          updateShooterPower();
          break;
        case 'U': liftUp = true; break;
        case 'O': liftDown = true; break;
        case 'H':
          baseSpeed = 1.0;
          Serial.println("⚡ Speed = HIGH");
          break;
        case 'h':
          baseSpeed = 0.3;
          Serial.println("🐢 Speed = LOW");
          break;
      }
    }

    // ขับมอเตอร์รวมทิศ
    for (int i = 0; i < 4; i++) {
      driveMotor(motorDIRPins[i], i, m[i]);
    }

    // ยิงลูก
    if (shootCmd) shootBall();
    if (stopShootingCmd) {
      ledcWrite(4, 0);
      ledcWrite(5, 0);
      shooting = false;
      digitalWrite(Cylinder_PUSH, LOW);
      Serial.println("⛔ หยุดชุดยิง");
    }

    // อัปเดตแขน
    updateLiftState();

    cmdBuffer = "";  // clear buffer
  }

  // non-block ยิง
  if (shooting && millis() - shootStartTime >= shootDuration) {
    digitalWrite(Cylinder_PUSH, LOW);
    shooting = false;
    Serial.println("✅ ยิงเสร็จแล้ว");
  }
}
