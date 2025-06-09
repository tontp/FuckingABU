import socket
import keyboard
import time
from datetime import datetime


class SimpleKeyboardClient:
    def __init__(self, host="192.168.0.214", port=8888):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False

        # สถานะการกดปุ่ม
        self.last_cmd = None
        self.space_was_pressed = False
        self.enter_was_pressed = False
        self.f_was_pressed = False
        self.up_arrow_pressed = False
        self.down_arrow_pressed = False
        self.j_was_pressed = False
        self.l_was_pressed = False

        # สถิติ
        self.stats = {
            "start_time": datetime.now(),
            "commands_sent": 0,
            "connection_count": 0,
        }

    def connect_to_server(self):
        """เชื่อมต่อไปยัง Raspberry Pi"""
        try:
            print(f"🔄 กำลังเชื่อมต่อไปยัง {self.host}:{self.port}...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.connected = True
            self.stats["connection_count"] += 1

            print(f"✅ เชื่อมต่อสำเร็จ!")
            print("🎮 พร้อมควบคุมหุ่นยนต์!")
            self.show_controls()
            return True

        except Exception as e:
            print(f"❌ ไม่สามารถเชื่อมต่อได้: {e}")
            return False

    def show_controls(self):
        """แสดงคำสั่งการควบคุม"""
        print("\n" + "=" * 60)
        print("🎮 คำสั่งการควบคุม")
        print("=" * 60)
        print("🚀 การเคลื่อนไหวพื้นฐาน:")
        print("   W = เดินหน้า    S = ถอยหลัง")
        print("   A = เลี้ยวซ้าย   D = เลี้ยวขวา")
        print("   Q = หมุนซ้าย    E = หมุนขวา")
        print("\n🔄 การเคลื่อนไหวแนวทแยง:")
        print("   W+A = เดินหน้าซ้าย    W+D = เดินหน้าขวา")
        print("   S+A = ถอยหลังซ้าย    S+D = ถอยหลังขวา")
        print("\n⚡ ฟังก์ชันพิเศษ:")
        print("   Space = ยิงกระบอกสูบ")
        print("   Enter = เปิด/ปิดชุดยิง")
        print("   ↑ = Linear UP")
        print("   ↓ = Linear DOWN")
        print("   F = ฟังก์ชันพิเศษ")
        print("\n❌ หยุดโปรแกรม: Ctrl+C")
        print("=" * 60 + "\n")
        print(" 🛡j: ยกที่รับบอลขึ้น \n")
        print("  🛡l: เอาที่รับบอลลง")

    def get_key(self):
        """ตรวจสอบปุ่มที่กดและส่งคืนคำสั่ง"""
        # ตรวจสอบ F key (toggle)
        if keyboard.is_pressed("f") and not self.f_was_pressed:
            self.f_was_pressed = True
            return "f"
        elif not keyboard.is_pressed("f"):
            self.f_was_pressed = False

        # ตรวจสอบการเคลื่อนไหวแนวทแยง (กดพร้อมกัน)
        if keyboard.is_pressed("w") and keyboard.is_pressed("a"):
            return "3"  # เดินหน้าซ้าย
        elif keyboard.is_pressed("w") and keyboard.is_pressed("d"):
            return "4"  # เดินหน้าขวา
        elif keyboard.is_pressed("s") and keyboard.is_pressed("a"):
            return "1"  # ถอยหลังซ้าย
        elif keyboard.is_pressed("s") and keyboard.is_pressed("d"):
            return "2"  # ถอยหลังขวา

        # ตรวจสอบการเคลื่อนไหวพื้นฐาน
        elif keyboard.is_pressed("w"):
            return "w"  # เดินหน้า
        elif keyboard.is_pressed("s"):
            return "s"  # ถอยหลัง
        elif keyboard.is_pressed("a"):
            return "a"  # เลี้ยวซ้าย
        elif keyboard.is_pressed("d"):
            return "d"  # เลี้ยวขวา
        elif keyboard.is_pressed("q"):
            return "q"  # หมุนซ้าย
        elif keyboard.is_pressed("e"):
            return "e"  # หมุนขวา

        # หยุด (ไม่กดปุ่มใดเลย)
        return "x"

    def get_command_description(self, char):
        """แปลงตัวอักษรเป็นคำอธิบาย"""
        commands = {
            "w": "เดินหน้า",
            "s": "ถอยหลัง",
            "a": "เลี้ยวซ้าย",
            "d": "เลี้ยวขวา",
            "x": "หยุด",
            "q": "หมุนซ้าย",
            "e": "หมุนขวา",
            "1": "ถอยซ้าย",
            "2": "ถอยขวา",
            "3": "เดินหน้าซ้าย",
            "4": "เดินหน้าขวา",
            " ": "ยิงกระบอกสูบ",
            "m": "เปิด/ปิดชุดยิง",
            "U": "Linear UP ON",
            "u": "Linear UP OFF",
            "O": "Linear DOWN ON",
            "o": "Linear DOWN OFF",
            "f": "ฟังก์ชันพิเศษ",
            "j": "ยกที่รับบอลขึ้น",
            "l": "เอาที่รับบอลลง",
        }
        return commands.get(char, "ไม่รู้จัก")

    def send_command(self, command):
        """ส่งคำสั่งไปยัง server"""
        if not self.connected or not self.sock:
            return False

        try:
            self.sock.send(command.encode())
            self.stats["commands_sent"] += 1

            desc = self.get_command_description(command)
            print(f"📤 ส่ง: '{command}' - {desc}")
            return True

        except Exception as e:
            print(f"❌ ไม่สามารถส่งคำสั่งได้: {e}")
            self.connected = False
            return False

    def handle_special_keys(self):
        """จัดการปุ่มพิเศษที่ต้องตรวจสอบแบบ toggle"""
        # Space bar (ยิงกระบอกสูบ)
        if keyboard.is_pressed("space") and not self.space_was_pressed:
            self.send_command(" ")
            self.space_was_pressed = True
        elif not keyboard.is_pressed("space"):
            self.space_was_pressed = False

        # Enter (เปิด/ปิดชุดยิง)
        if keyboard.is_pressed("enter") and not self.enter_was_pressed:
            self.send_command("m")
            self.enter_was_pressed = True
        elif not keyboard.is_pressed("enter"):
            self.enter_was_pressed = False

        # Up Arrow (Linear UP)
        if keyboard.is_pressed("up") and not self.up_arrow_pressed:
            self.send_command("U")
            self.up_arrow_pressed = True
        elif self.up_arrow_pressed and not keyboard.is_pressed("up"):
            self.send_command("u")
            self.up_arrow_pressed = False

        # Down Arrow (Linear DOWN)
        if keyboard.is_pressed("down") and not self.down_arrow_pressed:
            self.send_command("O")
            self.down_arrow_pressed = True
        elif self.down_arrow_pressed and not keyboard.is_pressed("down"):
            self.send_command("o")
            self.down_arrow_pressed = False

        # ปุ่ม j (ยกที่รับบอล)
        if keyboard.is_pressed("j") and not self.j_was_pressed:
            self.send_command("J")  # ยกที่รับบอลขึ้น
            self.j_was_pressed = True
        elif self.j_was_pressed and not keyboard.is_pressed("j"):
            self.send_command("j")  # หยุดยก
            self.j_was_pressed = False

        # ปุ่ม l (เอาที่รับบอลลง)
        if keyboard.is_pressed("l") and not self.l_was_pressed:
            self.send_command("L")  # เอาลง
            self.l_was_pressed = True
        elif self.l_was_pressed and not keyboard.is_pressed("l"):
            self.send_command("l")  # หยุด
            self.l_was_pressed = False

    def show_stats(self):
        """แสดงสถิติ"""
        uptime = datetime.now() - self.stats["start_time"]
        uptime_str = str(uptime).split(".")[0]

        print("\n" + "=" * 50)
        print("📊 สถิติการทำงาน")
        print("=" * 50)
        print(f"⏱️  เวลาทำงาน: {uptime_str}")
        print(f"📤 คำสั่งที่ส่ง: {self.stats['commands_sent']}")
        print(f"🔗 การเชื่อมต่อ: {self.stats['connection_count']}")
        print(f"🌐 สถานะ: {'✅ เชื่อมต่อ' if self.connected else '❌ ไม่เชื่อมต่อ'}")
        print("=" * 50 + "\n")

    def control_loop(self):
        """วนลูปหลักสำหรับควบคุม"""
        try:
            print("🚀 เริ่มระบบควบคุม - กด Ctrl+C เพื่อออก")

            while self.connected:
                # ตรวจสอบคำสั่งการเคลื่อนไหว
                cmd = self.get_key()

                # ส่งเฉพาะเมื่อคำสั่งเปลี่ยน
                if cmd != self.last_cmd:
                    if not self.send_command(cmd):
                        break
                    self.last_cmd = cmd

                # ตรวจสอบปุ่มพิเศษ
                self.handle_special_keys()

                # หน่วงเวลาเล็กน้อย
                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n⚠️  ได้รับสัญญาณหยุด (Ctrl+C)")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")

    def disconnect(self):
        """ตัดการเชื่อมต่อ"""
        if self.sock:
            try:
                # ส่งคำสั่งหยุดก่อนปิด
                self.sock.send(b"x")
                time.sleep(0.1)
                self.sock.close()
            except:
                pass

        self.connected = False
        print("🔌 ตัดการเชื่อมต่อแล้ว")

    def run(self):
        """รันโปรแกรมหลัก"""
        print("=" * 60)
        print("🎮 SIMPLE KEYBOARD ROBOT CONTROLLER")
        print("=" * 60)

        # รับ IP และ Port
        ip_input = input(f"Enter Raspberry Pi IP (default: {self.host}): ").strip()
        if ip_input:
            self.host = ip_input

        port_input = input(f"Enter port (default: {self.port}): ").strip()
        if port_input:
            try:
                self.port = int(port_input)
            except ValueError:
                print("❌ Port ไม่ถูกต้อง ใช้ค่า default")

        # เชื่อมต่อ
        if not self.connect_to_server():
            return

        try:
            # เริ่มควบคุม
            self.control_loop()
        finally:
            self.disconnect()
            self.show_stats()
            print("👋 ปิดโปรแกรม")


def main():
    # ตรวจสอบว่าติดตั้ง keyboard library แล้วหรือไม่
    try:
        import keyboard
    except ImportError:
        print("❌ กรุณาติดตั้ง keyboard library:")
        print("pip install keyboard")
        return

    client = SimpleKeyboardClient()
    client.run()


if __name__ == "__main__":
    main()
