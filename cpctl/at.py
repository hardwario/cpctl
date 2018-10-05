#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import serial


class ATException(Exception):
    '''Generic communication error exception.'''
    pass


class AT:
    '''Class AT communication with device.'''

    def __init__(self, device):
        '''Open device and flush buffers.'''
        exclusive = False if os.name == 'nt' or sys.platform == 'win32' else True
        self._device = device
        self._ser = None

    def _connect(self):
        if self._ser:
            return
        try:
            self._ser = serial.Serial(self._device, baudrate=115200, timeout=3)
        except Exception as e:
            raise ATException(str(e))

        time.sleep(0.1)
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        self._ser.write(b'\x1b')

    def _read_line(self):
        while True:
            line = self._ser.readline()
            if not line:
                raise ATException('Communication error occurred!')
            line = line.decode('ascii')

            # print("line:", repr(line))
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
        self._connect()
        self._ser.write(command.encode('ascii'))
        return self._read_response()
