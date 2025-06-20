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

        self.shoot_level = 0
        self.last_r1_state = False
        self.last_r2_state = False
        self.last_options_state = False
        self.square_state = False
        self.cross_last_state = False
        self.receive_toggle_state = False
        self.triangle_state = False
        self.base_speed_level = 1.0

        self.last_dpad_up_state = False
        self.last_dpad_down_state = False

        self.dualsense = pydualsense()
        self.dualsense.init()
        if not self.dualsense.connected:
            print("❌ ไม่พบจอย PS5")
            exit()

        self.menu_base_color = (255, 255, 255)
        self.dualsense.light.setColorI(*self.menu_base_color)

        self.last_sent_command = ""

    def connect_to_server(self):
        try:
            print(f"🔌 เชื่อมต่อไปยัง {self.host}:{self.port}...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.connected = True
            print("✅ เชื่อมต่อสำเร็จ!")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถเชื่อมต่อได้: {e}")
            return False

    def set_lightbar_color(self, level):
        if level == 0:
            self.dualsense.light.setColorI(*self.menu_base_color)
        elif level == 1:
            self.dualsense.light.setColorI(0, 255, 0)
        elif level == 2:
            self.dualsense.light.setColorI(255, 165, 0)
        elif level == 3:
            self.dualsense.light.setColorI(255, 0, 0)

    def get_commands(self):
        s = self.dualsense.state
        threshold = 20
        commands = set()

        # Movement
        lx, ly = s.LX, s.LY
        if ly < -30 - threshold:
            if lx < -30 - threshold:
                commands.add('6')
            elif lx > 30 + threshold:
                commands.add('7')
            else:
                commands.add('w')
        elif ly > 30 + threshold:
            if lx < -30 - threshold:
                commands.add('8')
            elif lx > 30 + threshold:
                commands.add('9')
            else:
                commands.add('s')
        elif lx < -30 - threshold:
            commands.add('a')
        elif lx > 30 + threshold:
            commands.add('d')

        rx = s.RX
        if rx < -30 - threshold:
            commands.add('q')
        elif rx > 30 + threshold:
            commands.add('e')

        # DpadUp → 'k' ส่งครั้งเดียว
        if getattr(s, 'DpadUp', False):
            if not self.last_dpad_up_state:
                commands.add('k')
                self.last_dpad_up_state = True
        else:
            self.last_dpad_up_state = False

        # DpadDown → 'l' ส่งครั้งเดียว
        if getattr(s, 'DpadDown', False):
            if not self.last_dpad_down_state:
                commands.add('l')
                self.last_dpad_down_state = True
        else:
            self.last_dpad_down_state = False

        # Shooting
        if s.R2:
            commands.add(' ')  # ยิง

        if s.circle:
            commands.add('b')  # เดาะ

        # Stop shooting
        if s.triangle:
            self.shoot_level = 0
            commands.add('z')
            self.dualsense.light.setColorI(*self.menu_base_color)

        # Set shooting level (R1)
        if s.R1:
            if not self.last_r1_state:
                self.shoot_level = (self.shoot_level + 1) % 4
                self.set_lightbar_color(self.shoot_level)
            self.last_r1_state = True
            commands.add(str(self.shoot_level))
        else:
            self.last_r1_state = False

        # Lift up/down (L1, L2)
        if s.L1:
            commands.add('U')  # ยกขึ้น
        if s.L2:
            commands.add('O')  # ยกลง

        # Speed toggle (Options)
        if hasattr(s, 'options'):
            if s.options and not self.last_options_state:
                self.base_speed_level = 1.0 if self.base_speed_level < 1.0 else 0.2
                if self.base_speed_level == 1.0:
                    self.menu_base_color = (128, 0, 128)
                    commands.add('H')
                else:
                    self.menu_base_color = (255, 255, 255)
                    commands.add('h')
                self.dualsense.light.setColorI(*self.menu_base_color)
            self.last_options_state = s.options

        # Misc toggle (Square)
        if s.square:
            if not getattr(self, 'square_last_state', False):
                self.square_state = not self.square_state
                self.square_last_state = True
                return 'M' if self.square_state else 'm'
        else:
            self.square_last_state = False

        # Receive toggle (Cross)
        if s.cross:
            if not self.cross_last_state:
                self.receive_toggle_state = not self.receive_toggle_state
                self.cross_last_state = True
                return 'N' if self.receive_toggle_state else 'n'
        else:
            self.cross_last_state = False

        if not commands:
            commands.add('x')  # หยุดถ้าไม่มีคำสั่ง

        return ''.join(sorted(commands))

    def send_command(self, command):
        if not self.connected:
            return False
        try:
            if command != self.last_sent_command:
                self.sock.send(command.encode())
                print(f"📤 ส่ง: {command}")
                self.last_sent_command = command
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถส่ง: {e}")
            self.connected = False
            return False

    def control_loop(self):
        print("🎮 เริ่มควบคุมด้วยจอย PS5 (Ctrl+C เพื่อหยุด)")
        try:
            while self.connected:
                cmd = self.get_commands()
                self.send_command(cmd)
                time.sleep(0.03)
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

if __name__ == "__main__":
    PS5ControllerClient().run()
