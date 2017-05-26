import sys
import struct
import time
from bluepy import btle

class Services(btle.Peripheral):
    # Bluepy's Peripheral class encapsulates a connection to a Bluetooth LE peripheral
    def __init__(self, mac):
        btle.Peripheral.__init__(self, mac)
        time.sleep(0.5)

    # Get the firmware version
    def firmware(self):
        hex_fw = self.readCharacteristic(0x17)
        fw = struct.unpack('<4h', hex_fw)
        return fw

    # Get the battery level
    def battery(self):
        hex_batt = self.readCharacteristic(0x11)
        batt = ord(hex_batt)
        return batt

    # Change the color of the logo and bar LEDs
    def set_leds(self, logo, line):
        self.writeCharacteristic(0x19, struct.pack('<8B', 6, 6, *(logo + line)))

    def vibrate(self, length):
        if length in range(1, 4):
            self.writeCharacteristic(0x19, struct.pack('<3B', 3, 1, length))

    # Suscribe to battery notifications
    def battery_notifications(self):
        self.writeCharacteristic(0x12, b'\x01\x10')

    # Suscribe to raw EMG notifications
    def emg_raw_notifications(self):
        self.writeCharacteristic(0x2c, b'\x01\x00')
        self.writeCharacteristic(0x2f, b'\x01\x00')
        self.writeCharacteristic(0x32, b'\x01\x00')
        self.writeCharacteristic(0x35, b'\x01\x00')

    # Suscribe to filtered EMG notifications
    def emg_filt_notifications(self):
        self.writeCharacteristic(0x28, b'\x01\x00')

    # Suscribe to IMU notifications
    def imu_notifications(self):
        self.writeCharacteristic(0x1d, b'\x01\x00')

    # Suscribe to classifier notifications
    def classifier_notifications(self):
        self.writeCharacteristic(0x24, b'\x02\x00')

    def set_mode(self, emg_mode, imu_mode, classifier_mode):
        command_string = struct.pack('<5B', 1, 3, emg_mode, imu_mode, classifier_mode)
        self.writeCharacteristic(0x19, command_string)

class Device(btle.DefaultDelegate):
    # bluepy functions which receive Bluetooth messages asynchronously,
    # such as notifications, indications, and advertising data
    def __init__(self, mac=None):
        btle.DefaultDelegate.__init__(self)
        self.services = Services(mac=get_myo(mac))
        self.services.setDelegate(self)

    def handleNotification(self, cHandle, data):
        # Notification handles of the 4 EMG data characteristics (raw)
        if cHandle == 0x2b or cHandle == 0x2e or cHandle == 0x31 or cHandle == 0x34:
            '''According to http://developerblog.myo.com/myocraft-emg-in-the-bluetooth-protocol/
            each characteristic sends two secuential readings in each update,
            so the received payload is split in two samples. According to the
            Myo BLE specification, the data type of the EMG samples is int8_t.
            '''
            emg1 = struct.unpack('<8b', data[:8])
            emg2 = struct.unpack('<8b', data[8:])
            print(emg1)
            print(emg2)
        # Notification handle of the EMG data characteristic (filtered)
        elif cHandle == 0x27:
            emg_filt = struct.unpack('<8H', data[:16])
            print(emg_filt)
        # Notification handle of the IMU data characteristic
        elif cHandle == 0x1c:
            values = struct.unpack('<10h', data)
            quat = [x/16384.0 for x in values[:4]]
            acc = [x/2048.0 for x in values[4:7]]
            gyro = [x/16.0 for x in values[7:10]]
            print(quat)
        # Notification handle of the battery data characteristic
        elif cHandle == 0x11:
            batt = ord(data)
            print("Battery level: %d" % batt)
        else:
            print('Data with unknown attr: %02X' % cHandle)

def get_myo(mac=None):
    if mac is not None:
        while True:
            for i in btle.Scanner(0).scan(1):
                if i.addr == mac:
                    return str(mac).upper()

    while True:
        for i in btle.Scanner(0).scan(1):
            for j in i.getScanData():
                if j[0] == 6 and j[2] == '4248124a7f2c4847b9de04a9010006d5':
                    return str(i.addr).upper()

class emg_mode:
    OFF = 0x00
    FILT = 0x01
    RAW = 0x02
    RAW_UNFILT = 0x03

class imu_mode:
    OFF = 0x00
    DATA = 0x01
    EVENTS = 0x02
    ALL = 0x03
    RAW = 0x04

class classifier_mode:
    OFF = 0x00
    ON = 0x01
