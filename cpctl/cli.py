#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''CLI module.'''

import datetime
import os
import sys
import time
import click
import re
import binascii
import zmq
from .at import AT, ATException

__version__ = '@@VERSION@@'


class CliException(Exception):
    '''Generic cli error exception.'''
    pass


def get_ports():
    if os.name == 'nt' or sys.platform == 'win32':
        from serial.tools.list_ports_windows import comports
    elif os.name == 'posix':
        from serial.tools.list_ports_posix import comports
    return sorted(comports())


def command(ctx, command):
    obj = ctx if isinstance(ctx, dict) else ctx.obj

    if 'command' in obj:
        return obj['command'](command)

    if obj['device']:
        at = AT(obj['device'])
        obj['command'] = at.command
        return at.command(command)

    elif obj['zmq']:
        context = zmq.Context()
        sock = context.socket(zmq.REQ)
        sock.connect('tcp://%s' % obj['zmq'])

        def zmq_command(command):
            sock.send_string(command)
            return sock.recv_json()
        obj['command'] = zmq_command
        return zmq_command(command)

    ports = get_ports()
    if not ports:
        raise CliException("Unknown device")

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
            raise CliException("Unknown device")

    at = AT(device)
    obj['command'] = at.command
    return at.command(command)


def is_node_in_list(ctx, serial):
    node_list = command(ctx, "$LIST")

    for row in node_list:
        s = row.split(',', 1)[0]
        if s == serial:
            return True
    return False


@click.group()
@click.option('--device', '-d', type=str, help='Device path.')
@click.option('--zmq', type=str, help='ZMQ')
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, device=None, zmq=None):
    '''Cooper Control Tool.'''
    ctx.obj['device'] = device
    ctx.obj['zmq'] = zmq


@cli.command()
def devices():
    '''Print available devices.'''
    for port in get_ports():
        click.echo(port[0], err=True)


@cli.group()
@click.pass_context
def node(ctx):
    '''Manage the nodes'''


@node.command("list")
@click.pass_context
def node_list(ctx):
    '''List attached nodes'''
    node_list = command(ctx, "$LIST")

    if node_list:
        for serial in node_list:
            click.echo(serial)
    else:
        click.echo("Empty list")


@node.command("attach")
@click.argument('serial')
@click.argument('key')
@click.option('--alias', 'alias', type=str, help='Set alias')
@click.pass_context
def node_attach(ctx, serial, key, alias=""):
    '''Attach node'''
    if not re.match("^[0-9]{16}$", serial):
        raise CliException("serial bad format")

    if not re.match("^[0-9abcdef]{32}$", key):
        raise CliException("serial key format")

    if is_node_in_list(ctx, serial):
        raise CliException("Node is in node list")

    if alias:
        command(ctx, '$ATTACH=%s,%s,"%s"' % (serial, key, alias))
    else:
        command(ctx, '$ATTACH=%s,%s' % (serial, key))

    command(ctx, "&W")

    click.echo('OK')


@node.command("detach")
@click.argument('serial')
@click.pass_context
def node_detach(ctx, serial):
    '''Detach node'''
    if not re.match("^[0-9]{16}$", serial):
        raise CliException("serial bad format")

    if not is_node_in_list(ctx, serial):
        raise CliException("Node is not in node list")

    command(ctx, "$DETACH=" + serial)
    command(ctx, "&W")
    click.echo('OK')


@node.command("purge")
@click.pass_context
def node_purge(ctx):
    '''Detach all nodes'''
    command(ctx, "$PURGE")
    command(ctx, "&W")
    click.echo('OK')


@cli.group()
@click.pass_context
def config(ctx):
    '''Config'''


@config.command('channel')
@click.option('--set', 'set_channel', type=int, help='New cahnnel')
@click.pass_context
def config_channel(ctx, set_channel=None):
    '''Channel'''
    if set_channel is not None:
        if set_channel < 0 or set_channel > 20:
            raise CliException("Bad channel range")

        command(ctx, "$CHANNEL=%d" % set_channel)
        command(ctx, "&W")

    click.echo(command(ctx, "$CHANNEL?")[0][1:])


@config.command('key')
@click.option('--set', 'key', type=str, help='Set 128-bit AES key', required=True)
@click.option('--generate', is_flag=True, help='Generate')
@click.option('--attach-to-device', 'attach_device', type=str)
@click.option('--attach-to-zmq', 'attach_zmq', type=str)
@click.pass_context
def config_channel(ctx, key=None, generate=False, attach_device=None, attach_zmq=None):
    '''128-bit AES key'''
    if key == '--generate':
        key = binascii.hexlify(os.urandom(16)).decode('ascii')

    if len(key) != 32:
        raise CliException("The bad length is expected 32 characters.")

    key = key.lower()

    command(ctx, "$KEY=%s" % key)
    command(ctx, "&W")

    serial = command(ctx, "+CGSN")[0][7:]

    if attach_device or attach_zmq:
        gwctx = {'device': attach_device, 'zmq': attach_zmq}
        if is_node_in_list(gwctx, serial):
            command(gwctx, "$DETACH=" + serial)
        command(gwctx, '$ATTACH=%s,%s' % (serial, key))
        command(gwctx, "&W")

    click.echo("%s %s" % (serial, key))


@cli.command('info')
@click.pass_context
def info(ctx):
    click.echo('Model: ' + command(ctx, "+CGMM")[0][7:])
    click.echo('ID:    ' + command(ctx, "+CGSN")[0][7:])


def main():
    '''Application entry point.'''
    try:
        cli(obj={}),
    except ATException as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except CliException as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
