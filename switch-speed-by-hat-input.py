#!/usr/bin/env python
import getopt
import os.path
import sys
import time
import minimalmodbus
import automationhat

NIBE_DEFAULT_CLIENT_ID = 30
NIBE_VENTILATION_SPEED_REG = 14
NIBE_SPEED_LOW = 0
NIBE_SPEED_MEDIUM = 1
NIBE_SPEED_HIGH = 2

def speed_to_text(speed):
    if speed == 0:
        return "Low"
    elif speed == 1:
        return "Medium"
    elif speed == 2:
        return "High"
    else:
        return "Unknown"


def init_modbus(device_file):
    instrument = minimalmodbus.Instrument('/dev/ttyUSB0', NIBE_DEFAULT_CLIENT_ID)
    instrument.serial.baudrate = 19200  # Baud
    instrument.serial.parity = minimalmodbus.serial.PARITY_EVEN
    return instrument

def read_nibe_ventilation_speed(instrument):
    ventilation_speed = instrument.read_register(NIBE_VENTILATION_SPEED_REG, 0) 
    print("Current ventilation speed: {}", ventilation_speed)
    if ventilation_speed in (NIBE_SPEED_LOW, NIBE_SPEED_MEDIUM, NIBE_SPEED_HIGH):
        return ventilation_speed
    else:
        raise Exception("Unknown ventilation speed: {}".format(ventilation_speed))

def switch_speed_to_low_if_not_already(current_speed, instrument):
    if current_speed != NIBE_SPEED_LOW:
        print("Switching speed to low")
        instrument.write_register(NIBE_VENTILATION_SPEED_REG, NIBE_SPEED_LOW, 0)
        print("Speed switched to low")
    else:
        print("Speed is already low, no need to switch")

def switch_speed_to_medium_if_not_already(current_speed, instrument):
    if current_speed != NIBE_SPEED_MEDIUM:
        print("Switching speed to medium")
        instrument.write_register(NIBE_VENTILATION_SPEED_REG, NIBE_SPEED_MEDIUM, 0)  # Registernumber, value, number of decimals, function code
        print("Speed switched to medium")
    else:
        print("Speed is already medium, no need to switch")

def usage():
    help_text = """
    Control Nibe ventilation speed by monitoring input switch state in automation hat input pin.
    Options:
     -h     Show help
     -i or --switch-input [number]  The number of the input pin (24v tolerant) to monitor (1, 2 or 3)
     -o or --output [number]        The output pin to rise when input is detected, for example, to light a LED
                                    to indicate a low fan speed setting.
     -m or --modbus-file            The device file for the RS485 RTU device connected to Nibe (default is
                                    /dev/ttyUSB0
    """
    print(help_text)
    exit(0)


def main(argv):
    input_pin_num = 1
    output_pin_num = 0
    modbus_device = "/dev/ttyUSB0"
    modbus_instrument = None
 
    opts, args = getopt.getopt(argv, "hi:o:m:", ["switch-input=", "output=", "modbus-file="])
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-i", "--switch-input"):
            if arg in ("1", "2", "3"):
                input_pin_num = int(arg)
            else:
                usage()
        elif opt in ("-o", "--output"):
            if arg in ("1", "2", "3"):
                output_pin_num = int(arg)
        elif opt in ("-m", "--modbus-file"):
            if os.path.isfile(arg):
                modbus_device = arg
            else:
                usage()

    if output_pin_num == 0:
        print("Output pin switching disabled!")

    if os.path.isfile(modbus_device):
        print("Modbus device file: ", modbus_device)
    else:
        print("Modbus device file not found: ", modbus_device)
        usage()
    
    print("Initializing modbus connection to device {}...", modbus_device)
    modbus_instrument = init_modbus(modbus_device)

    current_speed = read_nibe_ventilation_speed(modbus_device)
 #  If read speed is high, then assume that it has been set to high manually
 #  and from the low/medium speen switching perspective, we can treat that 
 #  state as medium speed. 
    if current_speed == NIBE_SPEED_HIGH:
        current_speed = NIBE_SPEED_MEDIUM;
    print("Current speed is: ", speed_to_text(current_speed))
 
    if automationhat.is_automation_hat():
        automationhat.light.power.write(1)
        print("Starting to listen state changes in input number {}", input_pin_num)
    else:
        print('Error! No automation HAT detected.');
        sys.exit(1)

    try:
        while True:
            input_pin_state = automationhat.input[input_pin_num].read()
            input_pin_state
            if input_pin_state == 1:
                print("Input pin {} is high, switching to medium speed", input_pin_num)
                switch_speed_to_low_if_not_already(current_speed, modbus_instrument)
                current_speed = NIBE_SPEED_LOW
            else:
                print("Input pin {} is low, switching to lower speed", input_pin_num)
                switch_speed_to_medium_if_not_already(current_speed, modbus_instrument)
                current_speed = NIBE_SPEED_MEDIUM
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        automationhat.light.power.write(0)
        sys.exit(0)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        automationhat.light.power.write(0)
        sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
