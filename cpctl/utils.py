#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import click
import zmq
from .at import AT, ATException


def get_ports():
    if os.name == 'nt' or sys.platform == 'win32':
        from serial.tools.list_ports_windows import comports
    elif os.name == 'posix':
        from serial.tools.list_ports_posix import comports
    return sorted(comports())


def create_at(ctx):
    obj = ctx if isinstance(ctx, dict) else ctx.obj

    if 'command' in obj:
        return

    if obj['device']:
        at = AT(obj['device'])
        obj['command'] = at.command
        return at

    elif obj['zmq']:
        context = zmq.Context()
        sock = context.socket(zmq.REQ)
        sock.connect('tcp://%s' % obj['zmq'])

        def zmq_command(command):
            sock.send_string(command)
            return sock.recv_json()
        obj['command'] = zmq_command
        return

    ports = get_ports()
    if not ports:
        ctx.fail("Unknown device.")

    for i, port in enumerate(ports):
        click.echo("%i %s" % (i, port[0]), err=True)
    d = click.prompt('Please enter device')
    for port in ports:
        if port[0] == d:
            device = port[0]
            break
    else:
        try:
            device = ports[int(d)][0]
        except Exception as e:
            ctx.fail("Unknown device.")

    at = AT(device)
    obj['command'] = at.command
    return at


def command(ctx, command):
    create_at(ctx)
    return ctx.obj['command'](command)
