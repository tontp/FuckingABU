#include <Arduino.h>

const int motorPWMPins[] = { 4, 14, 18, 17 };
const int motorDIRPins[] = { 15, 12, 19, 5 };

// ชุดยิง cytron 20A ชุดยิง
const int cytronPWM1 = 21;  //ledcWrite   channel 4
const int cytronDIR1 = 22;
const int cytronPWM2 = 23;  //ledcWrite   channel 5
const int cytronDIR2 = 2;

//relay Active HIGH
const int linear_UP = 32;      // ปรับองศา relay ch 1
const int linear_DOWN = 33;    // ปรับองศา relay ch 2
const int Cylinder_PUSH = 25;  // ดันบอลยิง   relay ch3

const int MAX_DUTY = 4095;

bool isFlipped = false;
bool shootingOn = false;

HardwareSerial UART_IN(1);  // UART1

char previousCmd = 'x';  // จำคำสั่งก่อนหน้า

void setup() {
  Serial.begin(115200);
  UART_IN.begin(115200, SERIAL_8N1, 16, -1);  // RX = 16

  for (int i = 0; i < 4; i++) {
    pinMode(motorDIRPins[i], OUTPUT);
    ledcSetup(i, 5000, 12);  // PWM channel i, 5 kHz, 12-bit
    ledcAttachPin(motorPWMPins[i], i);
    ledcWrite(i, 0);
  }

  Serial.println("ESP32 ตัวที่ 2 พร้อมควบคุมมอเตอร์");

  // Shooting setup
  ledcAttachPin(cytronPWM1, 4);
  ledcSetup(4, 5000, 12);
  ledcAttachPin(cytronPWM2, 5);
  ledcSetup(5, 5000, 12);
  pinMode(cytronDIR1, OUTPUT);
  pinMode(cytronDIR2, OUTPUT);
  pinMode(linear_UP, OUTPUT);
  pinMode(linear_DOWN, OUTPUT);
  pinMode(Cylinder_PUSH, OUTPUT);
}

void driveMotor(int dirPin, int pwmChannel, float power) {
  if (abs(power) < 0.01f) {
    digitalWrite(dirPin, LOW);
    ledcWrite(pwmChannel, 0);
    return;
  }
  bool forward = power > 0;
  digitalWrite(dirPin, forward ? HIGH : LOW);
  float duty = abs(power) * MAX_DUTY;
  if (duty > MAX_DUTY) duty = MAX_DUTY;
  ledcWrite(pwmChannel, int(duty));
}

void stopAll() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(motorDIRPins[i], LOW);
    ledcWrite(i, 0);
  }
}

void handleCommand(char cmd) {
  float m[4] = { 0, 0, 0, 0 };
  float speed = 0.6;
  float turn = 0.5;

  digitalWrite(linear_UP, LOW);
  digitalWrite(linear_DOWN, LOW);

  if (isFlipped) {
    speed = -speed;
    turn = -turn;
  }


  // ควบคุมความแรงชุดยิง
    if (cmd >= '0' && cmd <= '3') {
    int level = cmd - '0';
    int duty = 0;
    switch (level) {
      case 0: duty = 0; break;
      case 1: duty = MAX_DUTY / 4; break;
      case 2: duty = MAX_DUTY / 2; break;
      case 3: duty = MAX_DUTY; break;
    }
    ledcWrite(4, duty);
    ledcWrite(5, duty);
    digitalWrite(cytronDIR1, HIGH);
    digitalWrite(cytronDIR2, HIGH);
    Serial.printf("ชุดยิงระดับ %d, duty=%d\n", level, duty);
    return;
  }

  // --- ควบคุมรีเลย์ปรับองศา ---
  if (cmd == 'U') {
    digitalWrite(linear_UP, HIGH);
    return;
  } else if (cmd == 'u') {
    digitalWrite(linear_UP, LOW);
    return;
  } else if (cmd == 'O') {
    digitalWrite(linear_DOWN, HIGH);
    return;
  } else if (cmd == 'o') {
    digitalWrite(linear_DOWN, LOW);
    return;
  }

  switch (cmd) {
    case 'w':
      m[1] = -speed;
      m[2] = -speed;
      break;
    case 's':
      m[1] = speed;
      m[2] = speed;
      break;
    case 'a':
      m[1] = -speed;
      m[2] = speed;
      break;
    case 'd':
      m[1] = speed;
      m[2] = -speed;
      break;
    case '1':
      m[0] = -speed;
      m[3] = -speed;
      break;
    case '2':
      m[0] = -speed;
      m[3] = speed;
      break;
    case '3':
      m[0] = speed;
      m[3] = -speed;
      break;
    case '4':
      m[0] = speed;
      m[3] = speed;
      break;
    case 'q':
      m[0] = -turn;
      m[1] = -turn;
      m[2] = -turn;
      m[3] = -turn;
      break;
    case 'e':
      m[0] = turn;
      m[1] = turn;
      m[2] = turn;
      m[3] = turn;
      break;
    case 'f':
      isFlipped = !isFlipped;
      Serial.print("กลับทิศเป็น: ");
      Serial.println(isFlipped ? "กลับด้าน" : "ปกติ");
      stopAll();
      return;
    case 'x':
      stopAll();
      return;
    case ' ':
      digitalWrite(Cylinder_PUSH, HIGH);
      delay(800);
      digitalWrite(Cylinder_PUSH, LOW);
      Serial.println("ยิงกระบอกสูบ!");
      return;
    default:
      stopAll();
      return;
  }

  for (int i = 0; i < 4; i++) {
    driveMotor(motorDIRPins[i], i, m[i]);
  }
}

void loop() {
  if (UART_IN.available()) {
    char c = UART_IN.read();
    Serial.print("รับคำสั่ง: ");
    Serial.println(c);
    handleCommand(c);
    previousCmd = c;
  } else {
    // ✅ ถ้าก่อนหน้านี้เป็น A หรือ B และตอนนี้ไม่มีคำสั่งใหม่ → ปิดรีเลย์
    if (previousCmd == 'A' || previousCmd == 'B') {
      digitalWrite(linear_UP, LOW);
      digitalWrite(linear_DOWN, LOW);
      previousCmd = 'x';
    }
  }
}
