from pydualsense import pydualsense
import time

ds = pydualsense()
print(dir(ds))

dualsense = pydualsense()
dualsense.init()

if not dualsense.connected:
    print("ไม่พบจอย PS5 โปรดเชื่อมต่อก่อน")
    exit()

print("อ่านค่าจอย PS5... กด Ctrl+C เพื่อหยุด")

try:
    while True:
        s = dualsense.state
        
        # เช็คแค่ปุ่มที่กดหรือเลื่อนสติ๊ก
        buttons_pressed = []
        if s.cross: buttons_pressed.append("Cross")
        if s.circle: buttons_pressed.append("Circle")
        if s.square: buttons_pressed.append("Square")
        if s.triangle: buttons_pressed.append("Triangle")
        if s.L1: buttons_pressed.append("L1")
        if s.R1: buttons_pressed.append("R1")
        if s.L2Btn: buttons_pressed.append("L2Btn")
        if s.R2Btn: buttons_pressed.append("R2Btn")
        if s.DpadUp: buttons_pressed.append("DpadUp")
        if s.DpadDown: buttons_pressed.append("DpadDown")
        if s.DpadLeft: buttons_pressed.append("DpadLeft")
        if s.DpadRight: buttons_pressed.append("DpadRight")

        # เช็คสติ๊ก ถ้ามีการเคลื่อนไหว (ค่าไม่เป็น 0)
        if s.LX != 0 or s.LY != 0:
            buttons_pressed.append(f"LStick({s.LX},{s.LY})")
        if s.RX != 0 or s.RY != 0:
            buttons_pressed.append(f"RStick({s.RX},{s.RY})")

        if buttons_pressed:
            print("กด/เลื่อน:", ", ".join(buttons_pressed))

        time.sleep(0.1)

except KeyboardInterrupt:
    dualsense.close()
    print("ปิดการเชื่อมต่อจอยเรียบร้อยแล้ว")
