#include <Arduino.h>

// มอเตอร์ MDD10A (ขับเคลื่อน) - เรียง: m1, m2, m3, m4
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
bool isFlipped = false;

HardwareSerial UART_IN(1);
char previousCmd = 'x';

int shootingLevel = 0;  // ระดับความแรงของ Cytron 20A

void setup() {
  Serial.begin(115200);
  UART_IN.begin(115200, SERIAL_8N1, 16, -1);  // RX = 16

  for (int i = 0; i < 4; i++) {
    pinMode(motorDIRPins[i], OUTPUT);
    ledcSetup(i, 5000, 12);
    ledcAttachPin(motorPWMPins[i], i);
    ledcWrite(i, 0);
  }

  ledcSetup(4, 5000, 12);
  ledcAttachPin(cytronPWM1, 4);
  ledcSetup(5, 5000, 12);
  ledcAttachPin(cytronPWM2, 5);
  pinMode(cytronDIR1, OUTPUT);
  pinMode(cytronDIR2, OUTPUT);

  pinMode(linear_UP, OUTPUT);
  pinMode(linear_DOWN, OUTPUT);
  pinMode(Cylinder_PUSH, OUTPUT);

  Serial.println("✅ ESP32 ตัวที่ 2 พร้อมใช้งาน");
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

  Serial.printf("⚙️ ปรับระดับความแรงชุดยิงเป็น %d → duty=%d\n", shootingLevel, duty);
}

void handleCommand(char cmd) {
  float m[4] = { 0, 0, 0, 0 };
  float speed = 1.0;
  float turn = 1.0;

  if (isFlipped) {
    speed = -speed;
    turn = -turn;
  }

  if (cmd == 'L') {  // ปุ่ม L2 เพิ่มระดับความแรง
    shootingLevel = (shootingLevel + 1) % 4;
    updateShooterPower();
    stopAllMotors();
    return;
  }

  if (cmd == 'U') {
    digitalWrite(linear_UP, HIGH);
    digitalWrite(linear_DOWN, LOW);

  } else if (cmd == 'O') {
    digitalWrite(linear_DOWN, HIGH);
    digitalWrite(linear_UP, LOW);
  }

  // ยิงชุดยิงแบบกำหนดระดับตรง (0-3)
  if (cmd >= '0' && cmd <= '3') {
    shootingLevel = cmd - '0';
    updateShooterPower();
    stopAllMotors();
    return;
  }

  if (cmd == ' ') {
    digitalWrite(Cylinder_PUSH, HIGH);
    delay(800);
    digitalWrite(Cylinder_PUSH, LOW);
    Serial.println("✅ ยิงลูกบอล!");
    stopAllMotors();
    return;
  }

  if (cmd == 'f') {
    isFlipped = !isFlipped;
    Serial.print("🌀 โหมดกลับทิศ: ");
    Serial.println(isFlipped ? "กลับด้าน" : "ปกติ");
    stopAllMotors();
    return;
  }

  if (cmd == 'x') {
    stopAllMotors();
    digitalWrite(linear_DOWN, LOW);
    digitalWrite(linear_UP, LOW);
    return;
  }

  switch (cmd) {
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
      m[0] = turn;
      m[1] = turn;
      m[2] = turn;
      m[3] = turn;
      break;
    case 'e':
      m[0] = -turn;
      m[1] = -turn;
      m[2] = -turn;
      m[3] = -turn;
      break;
    case '7':
      m[0] = -speed;
      m[1] = speed;
      m[2] = speed;
      m[3] = -speed;
      break;
    case '6':
      m[0] = speed;
      m[1] = speed;
      m[2] = -speed;
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
    default: stopAllMotors(); return;
  }

  for (int i = 0; i < 4; i++) {
    driveMotor(motorDIRPins[i], i, m[i]);
  }
}

void loop() {
  if (UART_IN.available()) {
    char c = UART_IN.read();
    Serial.print("📥 คำสั่ง: ");
    Serial.println(c);
    handleCommand(c);
    previousCmd = c;
  }
}
