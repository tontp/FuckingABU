import serial
import keyboard
import time

ser = serial.Serial("COM7", 115200)

last_cmd = None
space_was_pressed = False
enter_was_pressed = False
f_was_pressed = False
up_arrow_pressed = False
down_arrow_pressed = False

def get_key():
    global f_was_pressed

    if keyboard.is_pressed('f'):
        if not f_was_pressed:
            f_was_pressed = True
            return 'f'
    else:
        f_was_pressed = False

    if keyboard.is_pressed('w') and keyboard.is_pressed('a'):
        return '3'
    elif keyboard.is_pressed('w') and keyboard.is_pressed('d'):
        return '4'
    elif keyboard.is_pressed('s') and keyboard.is_pressed('a'):
        return '1'
    elif keyboard.is_pressed('s') and keyboard.is_pressed('d'):
        return '2'
    elif keyboard.is_pressed('w'):
        return 'w'
    elif keyboard.is_pressed('s'):
        return 's'
    elif keyboard.is_pressed('a'):
        return 'a'
    elif keyboard.is_pressed('d'):
        return 'd'
    elif keyboard.is_pressed('q'):
        return 'q'
    elif keyboard.is_pressed('e'):
        return 'e'

    return 'x'

try:
    while True:
        cmd = get_key()

        if cmd != last_cmd:
            ser.write(cmd.encode())
            print(f"ส่ง: {cmd}")
            last_cmd = cmd

        # Spacebar ยิงกระบอกสูบ
        if keyboard.is_pressed('space'):
            if not space_was_pressed:
                ser.write(b' ')
                print("ส่ง: ยิงกระบอกสูบ")
                space_was_pressed = True
        else:
            space_was_pressed = False

        # Enter เปิด/ปิดชุดยิง
        if keyboard.is_pressed('enter'):
            if not enter_was_pressed:
                ser.write(b'm')
                print("ส่ง: เปิด/ปิดชุดยิง")
                enter_was_pressed = True
        else:
            enter_was_pressed = False

        # ลูกศรขึ้น (Up Arrow)
        if keyboard.is_pressed('up'):
            if not up_arrow_pressed:
                ser.write(b'U')
                print("ส่ง: linear_UP ON")
                up_arrow_pressed = True
        else:
            if up_arrow_pressed:
                ser.write(b'u')
                print("ส่ง: linear_UP OFF")
                up_arrow_pressed = False

        # ลูกศรลง (Down Arrow)
        if keyboard.is_pressed('down'):
            if not down_arrow_pressed:
                ser.write(b'D')
                print("ส่ง: linear_DOWN ON")
                down_arrow_pressed = True
        else:
            if down_arrow_pressed:
                ser.write(b'd')
                print("ส่ง: linear_DOWN OFF")
                down_arrow_pressed = False

        time.sleep(0.05)

except KeyboardInterrupt:
    ser.close()
    print("ปิดโปรแกรม")
