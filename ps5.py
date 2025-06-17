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
        self.last_l2_state = False

        self.square_state = False
        self.cross_last_state = False
        self.receive_toggle_state = False
        self.triangle_last_state = False
        self.lift_toggle_state = False
        self.last_r1_state = False
        self.last_r2_state = False

        self.stats = {
            'start_time': datetime.now(),
            'commands_sent': 0,
            'connection_count': 0
        }

        self.dualsense = pydualsense()
        self.dualsense.init()
        if not self.dualsense.connected:
            print("❌ ไม่พบจอย PS5")
            exit()
        self.dualsense.light.setColorI(0, 0, 255)  # ฟ้า

    def connect_to_server(self):
        try:
            print(f"🔌 เชื่อมต่อไปยัง {self.host}:{self.port}...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.connected = True
            self.stats['connection_count'] += 1
            print("✅ เชื่อมต่อสำเร็จ!")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถเชื่อมต่อได้: {e}")
            return False

    def set_lightbar_color(self, level):
        if level == 0:
            self.dualsense.light.setColorI(0, 0, 255)
        elif level == 1:
            self.dualsense.light.setColorI(0, 255, 0)
        elif level == 2:
            self.dualsense.light.setColorI(255, 165, 0)
        elif level == 3:
            self.dualsense.light.setColorI(255, 0, 0)

    def get_command_from_controller(self):
        s = self.dualsense.state
        lx, ly = s.LX, s.LY
        rx, ry = s.RX, s.RY
        threshold = 20

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

        if getattr(s, 'DpadUp', False): return 'w'
        if getattr(s, 'DpadRight', False): return 'd'
        if getattr(s, 'DpadDown', False): return 's'
        if getattr(s, 'DpadLeft', False): return 'a'

        # toggle lift (k/l) – ป้องกันสั่งซ้ำ
        if s.triangle:
            if not self.triangle_last_state and self.last_cmd not in ['k', 'l']:
                self.lift_toggle_state = not self.lift_toggle_state
                self.triangle_last_state = True
                return 'k' if self.lift_toggle_state else 'l'
        else:
            self.triangle_last_state = False

        if s.circle:
            return 'b'

        if s.L1:
            return ' '

        if s.square:
            if not getattr(self, 'square_last_state', False):
                self.square_state = not self.square_state
                self.square_last_state = True
                return 'M' if self.square_state else 'm'
        else:
            self.square_last_state = False

        if s.cross:
            if not self.cross_last_state:
                self.receive_toggle_state = not self.receive_toggle_state
                self.cross_last_state = True
                return 'N' if self.receive_toggle_state else 'n'
        else:
            self.cross_last_state = False

        if s.touchBtn:
            return 'f'

        if s.R1:
            self.last_r1_state = True
            return 'U'
        elif self.last_r1_state:
            self.last_r1_state = False
            return 'x'

        if s.R2:
            self.last_r2_state = True
            return 'O'
        elif self.last_r2_state:
            self.last_r2_state = False
            return 'x'

        if s.L2Btn and not self.last_l2_state:
            self.shoot_level = (self.shoot_level + 1) % 4
            self.set_lightbar_color(self.shoot_level)
            self.last_l2_state = True
            return str(self.shoot_level)
        elif not s.L2Btn:
            self.last_l2_state = False

        return 'x'

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
        print("🎮 เริ่มควบคุมด้วยจอย PS5 (Ctrl+C เพื่อหยุด)")
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
