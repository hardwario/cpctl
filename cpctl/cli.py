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
    if 'command' in ctx.obj:
        return ctx.obj['command'](command)

    if ctx.obj['device']:
        at = AT(ctx.obj['device'])
        ctx.obj['command'] = at.command
        return at.command(command)

    elif ctx.obj['zmq']:
        context = zmq.Context()
        sock = context.socket(zmq.REQ)
        sock.connect('tcp://%s' % ctx.obj['zmq'])

        def zmq_command(command):
            sock.send_string(command)
            return sock.recv_json()
        ctx.obj['command'] = zmq_command
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
    ctx.obj['command'] = at.command
    return at.command(command)


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
@click.pass_context
def node_attach(ctx, serial, key):
    '''Attach node'''
    if not re.match("^[0-9]{16}$", serial):
        raise CliException("serial bad format")

    if not re.match("^[0-9abcdef]{32}$", key):
        raise CliException("serial key format")

    node_list = command(ctx, "$LIST")

    if serial in node_list:
        raise CliException("Node is in node list")

    command(ctx, "$ATTACH=%s,%s" % (serial, key))
    command(ctx, "&W")

    click.echo('OK')


@node.command("detach")
@click.argument('serial')
@click.pass_context
def node_detach(ctx, serial):
    '''Detach node'''
    if not re.match("^[0-9]{16}$", serial):
        raise CliException("serial bad format")

    node_list = command(ctx, "$LIST")

    if serial not in node_list:
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
@click.pass_context
def config_channel(ctx, key=None, generate=False):
    '''128-bit AES key'''
    if key == '--generate':
        key = binascii.hexlify(os.urandom(16)).decode('ascii')

    if len(key) != 32:
        raise CliException("The bad length is expected 32 characters.")

    key = key.lower()

    click.echo("Set key: %s" % key)

    command(ctx, "$KEY=%s" % key)
    command(ctx, "&W")

    click.echo('OK')


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
