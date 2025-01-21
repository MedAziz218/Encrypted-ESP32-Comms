import serial
import time
import sys
def read_serial(port, baudrate, timeout):
    print("opening serial port ...")
    # ser = serial.Serial(port, baudrate, timeout=timeout)
    connected = False

    try:
        ser = serial.Serial(
            port, baudrate,timeout= 0.5
        )  # Start communications with the bluetooth unit
        ser.flushInput()  # This gives the bluetooth a little kick
        connected = True
    except:
        print("Could not Connect")
        connected = False
        return


    end_time = time.time() + 60  # Read for 1 minute
    incoming_msg_counter = 0
    try:
        while time.time() < end_time:

            op = ser.isOpen()
            if not op :
                raise Exception("Connection Lost")
            if ser.in_waiting  and op:
                input_data = b''
                dt = int(time.time() * 1_000_000)  # time in microseconds
                while ser.in_waiting:
                    input_data += ser.read(size=ser.in_waiting)
                # input_data = ser.readline()
                dt = int(time.time() * 1_000_000) -dt
                ser.flushInput()

                # This reads the incoming data. In this particular example it will be the "Bluetooth answers" line
                # input_str = input_data.decode()
                input_str = input_data.decode('utf-8', errors='ignore')

                print(f"{dt}>> {input_str.strip()}")  # These are bytes coming in so a decode is needed

            incoming_msg_counter += 1
            time.sleep(0.001)  # A pause between bursts
    except Exception as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        if ser.isOpen():
            print(">> closing ...")
            ser.flushInput()
            ser.flushOutput()
            ser.close()
            print("Serial port closed")
            quit()
    finally:
        if ser.isOpen():
            print(">> closing ...")
            ser.flushInput()
            ser.flushOutput()
            ser.close()
            print("Serial port closed")
            quit()

if __name__ == "__main__":
    read_serial('COM5', 9600, 0)
    quit()