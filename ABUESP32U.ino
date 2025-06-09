#include <HardwareSerial.h>

HardwareSerial SerialUART(1);  // UART1

void setup() {
  Serial.begin(115200);
  SerialUART.begin(115200, SERIAL_8N1, -1, 17); // TX = 17, ไม่มี RX
  Serial.println("ESP32 ตัวที่ 1 พร้อมส่งข้อมูลผ่าน UART");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    Serial.print("รับคำสั่งจากคอม: ");
    Serial.println(cmd);
    SerialUART.write(cmd);  // ส่งผ่าน UART ไปยัง ESP32 ตัวที่ 2
  }
}
