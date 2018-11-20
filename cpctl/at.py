#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import serial
import platform
from ctypes import *
try:
    import fcntl
except ImportError:
    fcntl = None


class ATException(Exception):
    '''Generic communication error exception.'''
    pass


class AT:
    '''Class AT communication with device.'''

    def __init__(self, device, debug=False):
        '''Open device and flush buffers.'''
        exclusive = False if os.name == 'nt' or sys.platform == 'win32' else True
        self._device = device
        self._ser = None
        self._debug = debug

    def _connect(self):
        if self._ser:
            return
        try:
            self._ser = serial.Serial(self._device,
                                      baudrate=115200,
                                      bytesize=serial.EIGHTBITS,
                                      parity=serial.PARITY_NONE,
                                      stopbits=serial.STOPBITS_ONE,
                                      timeout=1,
                                      xonxoff=False,
                                      rtscts=False,
                                      dsrdtr=False)
        except serial.serialutil.SerialException as e:
            if e.errno == 2:
                raise ATException('Could not open device %s' % device)
            raise ATException(str(e))

        self._lock()
        self._speed_up()

        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        time.sleep(0.1)
        self._ser.write(b'\x1b')

    def __del__(self):
        self._unlock()
        try:
            self._ser.close()
        except Exception as e:
            pass
        self._ser = None

    def _read_line(self):
        while True:
            line = self._ser.readline()
            if not line:
                raise ATException('Communication error occurred!')
            line = line.decode('ascii')

            if self._debug:
                print("RX :", repr(line))
            if line[0] == '{':
                continue
            if line[0] == '#':
                continue
            return line.strip()

    def _read_response(self):
        response = []
        while True:
            line = self._read_line()
            if line == 'OK':
                return response
            elif line == 'ERROR':
                raise ATException('Received ERROR')
            else:
                response.append(line)

    def command(self, command):
        command = 'AT' + command + '\r\n'
        command = command.encode('ascii')
        if self._debug:
            print('TX:', repr(command))
        self._connect()
        self._ser.write(command)
        return self._read_response()

    def _lock(self):
        if fcntl or not self._ser:
            return
        try:
            fcntl.flock(self._ser.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception as e:
            raise ATException('Could not lock device %s' % self._device)

    def _unlock(self):
        if not fcntl or not self._ser:
            return
        fcntl.flock(self._ser.fileno(), fcntl.LOCK_UN)

    def _speed_up(self):
        if not fcntl:
            return
        if platform.system() != 'Linux':
            return

        TIOCGSERIAL = 0x0000541E
        TIOCSSERIAL = 0x0000541F
        ASYNC_LOW_LATENCY = 0x2000

        class serial_struct(Structure):
            _fields_ = [("type", c_int),
                        ("line", c_int),
                        ("port", c_uint),
                        ("irq", c_int),
                        ("flags", c_int),
                        ("xmit_fifo_size", c_int),
                        ("custom_divisor", c_int),
                        ("baud_base", c_int),
                        ("close_delay", c_ushort),
                        ("io_type", c_byte),
                        ("reserved_char", c_byte * 1),
                        ("hub6", c_uint),
                        ("closing_wait", c_ushort),
                        ("closing_wait2", c_ushort),
                        ("iomem_base", POINTER(c_ubyte)),
                        ("iomem_reg_shift", c_ushort),
                        ("port_high", c_int),
                        ("iomap_base", c_ulong)]

        buf = serial_struct()

        try:
            fcntl.ioctl(self._ser.fileno(), TIOCGSERIAL, buf)
            buf.flags |= ASYNC_LOW_LATENCY
            fcntl.ioctl(self._ser.fileno(), TIOCSSERIAL, buf)
        except Exception as e:
            pass

    def ftdi_reset_sequence(self, timeout=0.1):
        self._connect()
        self._ser.rts = True
        self._ser.dtr = False
        time.sleep(timeout)
        self._ser.rts = False
