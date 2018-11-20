#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import serial
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
            self._ser = serial.Serial(self._device, baudrate=115200, timeout=3)
        except Exception as e:
            raise ATException(str(e))

        self._lock()
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

