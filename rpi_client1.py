import socket
import serial
import time
import threading
from datetime import datetime

class TCPSerialBridge:
    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=115200, tcp_port=8888):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.tcp_port = tcp_port

        # Serial connection
        self.ser = None
        self.serial_connected = False

        # TCP connection
        self.server_socket = None
        self.client_socket = None
        self.client_addr = None
        self.tcp_connected = False

        # Statistics
        self.stats = {
            'start_time': datetime.now(),
            'total_received': 0,
            'total_sent_to_esp32': 0,
            'connection_count': 0
        }

    def setup_serial(self):
        """ตั้งค่าการเชื่อมต่อ Serial"""
        try:
            print(f"🔌 เชื่อมต่อ Serial: {self.serial_port} @ {self.baud_rate} baud")
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            time.sleep(2)  # รอให้ ESP32 boot
            self.serial_connected = True
            print("✅ Serial เชื่อมต่อสำเร็จ")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถเชื่อมต่อ Serial: {e}")
            return False

    def setup_tcp_server(self):
        """ตั้งค่า TCP Server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.tcp_port))
            self.server_socket.listen(1)
            print(f"🌐 TCP Server เริ่มทำงานที่พอร์ต {self.tcp_port}")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถสร้าง TCP Server: {e}")
            return False

    def wait_for_client(self):
        """รอการเชื่อมต่อจาก client"""
        try:
            print("⏳ รอการเชื่อมต่อจากโน้ตบุ๊ก...")
            self.client_socket, self.client_addr = self.server_socket.accept()
            self.tcp_connected = True
            self.stats['connection_count'] += 1

            print(f"✅ เชื่อมต่อจาก: {self.client_addr}")
            print("🎮 พร้อมรับคำสั่งควบคุม!")
            return True
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดขณะรอ client: {e}")
            return False

    def handle_client_data(self):
        """จัดการข้อมูลจาก client"""
        try:
            while self.tcp_connected and self.serial_connected:
                # รับข้อมูลทีละ byte
                data = self.client_socket.recv(1)

                if not data:
                    print("🔌 Client ตัดการเชื่อมต่อ")
                    break

                # แสดงข้อมูลที่ได้รับ
                char = data.decode('utf-8', errors='ignore')
                self.stats['total_received'] += 1

                # แปลงคำสั่งให้เข้าใจง่าย
                command_desc = self.get_command_description(char)
                print(f"📨 ได้รับ: '{char}' ({ord(char)}) - {command_desc}")

                # ส่งไปยัง ESP32
                if self.ser and self.serial_connected:
                    self.ser.write(data)
                    self.stats['total_sent_to_esp32'] += 1
                    print(f"📤 ส่งไป ESP32: '{char}'")
                else:
                    print("❌ Serial ไม่พร้อม - ไม่สามารถส่งไป ESP32")

        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดขณะจัดการข้อมูล: {e}")
        finally:
            self.cleanup_client()

    def get_command_description(self, char):
        """แปลงตัวอักษรเป็นคำอธิบายคำสั่ง"""
        commands = {
            'w': 'เดินหน้า',
            's': 'ถอยหลัง',
            'a': 'เลี้ยวซ้าย',
            'd': 'เลี้ยวขวา',
            'x': 'หยุด',
            'q': 'หมุนซ้าย',
            'e': 'หมุนขวา',
            '1': 'ถอยซ้าย',
            '2': 'ถอยขวา',
            '3': 'เดินหน้าซ้าย',
            '4': 'เดินหน้าขวา',
            ' ': 'ยิงกระบอกสูบ',
            'm': 'เปิด/ปิดชุดยิง',
            'U': 'Linear UP ON',
            'u': 'Linear UP OFF',
            'O': 'Linear DOWN ON',
            'o': 'Linear DOWN OFF',
            'f': 'ฟังก์ชันพิเศษ'
        }
        return commands.get(char, 'ไม่รู้จักคำสั่ง')

    def cleanup_client(self):
        """ทำความสะอาดการเชื่อมต่อ client"""
        self.tcp_connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        print("🔌 ปิดการเชื่อมต่อ client")

    def show_stats(self):
        """แสดงสถิติการทำงาน"""
        uptime = datetime.now() - self.stats['start_time']
        uptime_str = str(uptime).split('.')[0]

        print("\n" + "="*50)
        print("📊 สถิติการทำงาน")
        print("="*50)
        print(f"⏱️  เวลาทำงาน: {uptime_str}")
        print(f"📨 ข้อมูลที่ได้รับ: {self.stats['total_received']}")
        print(f"📤 ส่งไป ESP32: {self.stats['total_sent_to_esp32']}")
        print(f"🔗 จำนวนการเชื่อมต่อ: {self.stats['connection_count']}")
        print(f"🌐 TCP: {'✅ เชื่อมต่อ' if self.tcp_connected else '❌ ไม่เชื่อมต่อ'}")
        print(f"📡 Serial: {'✅ เชื่อมต่อ' if self.serial_connected else '❌ ไม่เชื่อมต่อ'}")
        print("="*50 + "\n")

    def monitor_system(self):
        """แสดงสถานะระบบทุก 30 วินาที"""
        while True:
            try:
                time.sleep(30)
                self.show_stats()
            except:
                break

    def run(self):
        """รันโปรแกรมหลัก"""
        print("="*60)
        print("🚀 TCP to Serial Bridge สำหรับควบคุมหุ่นยนต์")
        print("="*60)

        # ตั้งค่า Serial
        if not self.setup_serial():
            print("❌ ไม่สามารถเริ่มระบบได้ - ตรวจสอบ Serial connection")
            return

        # ตั้งค่า TCP Server
        if not self.setup_tcp_server():
            print("❌ ไม่สามารถเริ่มระบบได้ - ตรวจสอบ TCP port")
            return

        # เริ่ม monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
        monitor_thread.start()

        try:
            # วนลูปรอ client เชื่อมต่อ
            while True:
                if self.wait_for_client():
                    self.handle_client_data()

                # รอก่อนรับ client ใหม่
                print("⏳ รอการเชื่อมต่อใหม่...")
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n⚠️  ได้รับสัญญาณหยุดโปรแกรม (Ctrl+C)")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดร้าย serious: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """ทำความสะอาดเมื่อปิดโปรแกรม"""
        print("\n🛑 กำลังปิดระบบ...")

        self.cleanup_client()

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            print("🌐 ปิด TCP Server")

        if self.ser and self.serial_connected:
            try:
                # ส่งคำสั่งหยุดก่อนปิด
                self.ser.write(b'x')
                time.sleep(0.1)
                self.ser.close()
            except:
                pass
            print("📡 ปิด Serial connection")

        self.show_stats()
        print("✅ ปิดระบบเรียบร้อย")

def main():
    # กำหนดพารามิเตอร์ตามต้องการ
    SERIAL_PORT = '/dev/ttyUSB0'  # เปลี่ยนตามพอร์ตที่ใช้
    BAUD_RATE = 115200
    TCP_PORT = 8888

    print("⚙️  กำลังเริ่มต้นระบบ...")
    bridge = TCPSerialBridge(SERIAL_PORT, BAUD_RATE, TCP_PORT)
    bridge.run()

if __name__ == "__main__":
    main()
