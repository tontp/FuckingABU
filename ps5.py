from pydualsense import pydualsense
import socket
import time
from datetime import datetime

class PS5ControllerClient:
    def __init__(self, host="192.168.0.214", port=8889):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.last_cmd = None
        self.shoot_level = 0
        self.last_l2_state = False  # สำหรับเช็คว่ากด L2 แค่ครั้งเดียว
        self.square_state = False   # สถานะสลับของปุ่มสี่เหลี่ยม

        self.stats = {
            'start_time': datetime.now(),
            'commands_sent': 0,
            'connection_count': 0
        }

        # เริ่มต้นจอยด้วย pydualsense
        self.dualsense = pydualsense()
        self.dualsense.init()
        if not self.dualsense.connected:
            print("❌ ไม่พบจอย PS5")
            exit()
        self.dualsense.light.setColorI(0,0,255)  # ตั้งสีฟ้าเริ่มต้น

    def connect_to_server(self):
        try:
            print(f"🔌 เชื่อมต่อไปยัง {self.host}:{self.port}...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.connected = True
            self.stats['connection_count'] += 1
            print("✅ เชื่อมต่อสำเร็จ! 🎮 พร้อมควบคุม")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถเชื่อมต่อได้: {e}")
            return False

    def set_lightbar_color(self, level):
        if level == 0:
            self.dualsense.light.setColorI(0, 0, 255)     # ฟ้า
        elif level == 1:
            self.dualsense.light.setColorI(0, 255, 0)     # เขียว
        elif level == 2:
            self.dualsense.light.setColorI(255, 165, 0)   # ส้ม
        elif level == 3:
            self.dualsense.light.setColorI(255, 0, 0)     # แดง

    def get_command_from_controller(self):
        s = self.dualsense.state
        lx, ly = s.LX, s.LY
        rx, ry = s.RX, s.RY
        threshold = 20

        # สติ๊กซ้ายควบคุมทิศทาง (ตัวอย่าง)
        if ly < -30 - threshold:
            if lx < -30 - threshold:
                return '6'
            elif lx > 30 + threshold:
                return '7'
            else:
                return 'w'
        elif ly > 30 + threshold:
            if lx < -30 - threshold:
                return '8'
            elif lx > 30 + threshold:
                return '9'
            else:
                return 's'
        elif lx < -30 - threshold:
            return 'a'
        elif lx > 30 + threshold:
            return 'd'
        elif rx < -30 - threshold:
            return 'q'
        elif rx > 30 + threshold:
            return 'e'

        # ปุ่มอื่นๆ
        if s.triangle:   # กดสามเหลี่ยม -> ยกขึ้น
            return 'k'
        if s.cross:      # กด x -> ยกลง
            return 'l'
        if s.circle:
            return 'b'
        if s.L1:
            return ' '
        
        # ปุ่มสี่เหลี่ยม กดครั้งแรกส่ง 'M' ครั้งที่สองส่ง 'm' สลับกัน
        if s.square:
            if not getattr(self, 'square_last_state', False):
                self.square_state = not self.square_state
                self.square_last_state = True
                if self.square_state:
                    return 'M'  # HIGH
                else:
                    return 'm'  # LOW
        else:
            self.square_last_state = False

        if s.touchBtn:
            return 'f'

        # R1 และ R2 ควบคุม linear_UP / linear_DOWN
        if s.R1:
            return 'U'
        if s.R2:
            return 'O'

        # ปรับระดับมอเตอร์ด้วย L2 (กดทีละครั้ง)
        if s.L2Btn and not self.last_l2_state:
            self.shoot_level = (self.shoot_level + 1) % 4
            self.set_lightbar_color(self.shoot_level)
            self.last_l2_state = True
            return str(self.shoot_level)
        elif not s.L2Btn:
            self.last_l2_state = False

        # D-pad (สำรอง)
        if getattr(s, 'DpadUp', False):
            return 'w'
        if getattr(s, 'DpadRight', False):
            return 'd'
        if getattr(s, 'DpadDown', False):
            return 's'
        if getattr(s, 'DpadLeft', False):
            return 'a'
        if getattr(s, 'DpadUp', False) and getattr(s, 'DpadRight', False):
            return '6'
        if getattr(s, 'DpadUp', False) and getattr(s, 'DpadLeft', False):
            return '7'
        if getattr(s, 'DpadDown', False) and getattr(s, 'DpadRight', False):
            return '8'
        if getattr(s, 'DpadDown', False) and getattr(s, 'DpadLeft', False):
            return '9'

        return 'x'  # ไม่กดอะไรเลย

    def send_command(self, command):
        if not self.connected:
            return False
        try:
            self.sock.send(command.encode())
            self.stats['commands_sent'] += 1
            print(f"📤 ส่ง: {command}")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถส่ง: {e}")
            self.connected = False
            return False

    def control_loop(self):
        print("🎮 เริ่มควบคุมด้วยจอย PS5 (กด Ctrl+C เพื่อหยุด)")
        try:
            while self.connected:
                cmd = self.get_command_from_controller()
                if cmd != self.last_cmd:
                    self.send_command(cmd)
                    self.last_cmd = cmd
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\n🛑 หยุดระบบ")
        finally:
            self.disconnect()

    def disconnect(self):
        if self.sock:
            try:
                self.sock.send(b'x')
                self.sock.close()
            except:
                pass
        self.dualsense.close()
        self.connected = False
        print("🔌 ตัดการเชื่อมต่อแล้ว")

    def run(self):
        if not self.connect_to_server():
            return
        self.control_loop()
        print("📊 คำสั่งทั้งหมด:", self.stats['commands_sent'])
        print("👋 จบการทำงาน")

if __name__ == "__main__":
    PS5ControllerClient().run()
