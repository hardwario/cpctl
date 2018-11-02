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


def select_device(ctx):
    if 'at' not in ctx.obj:
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

        ctx.obj['at'] = AT(device)


@click.group()
@click.option('--device', '-d', type=str, help='Device path.')
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, device=None):
    '''Cooper Control Tool.'''
    if device:
        ctx.obj['at'] = AT(device)


@cli.command()
def devices():
    '''Print available devices.'''
    for port in get_ports():
        click.echo(port[0], err=True)


@cli.group()
@click.pass_context
def node(ctx):
    '''Manage the nodes'''
    select_device(ctx)


@node.command("list")
@click.pass_context
def node_list(ctx):
    '''List attached nodes'''
    node_list = ctx.obj['at'].command("$LIST")

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

    node_list = ctx.obj['at'].command("$LIST")

    if serial in node_list:
        raise CliException("Node is in node list")

    ctx.obj['at'].command("$ATTACH=%s,%s" % (serial, key))
    ctx.obj['at'].command("&W")

    click.echo('OK')


@node.command("detach")
@click.argument('serial')
@click.pass_context
def node_detach(ctx, serial):
    '''Detach node'''
    if not re.match("^[0-9]{16}$", serial):
        raise CliException("serial bad format")

    node_list = ctx.obj['at'].command("$LIST")

    if serial not in node_list:
        raise CliException("Node is not in node list")

    ctx.obj['at'].command("$DETACH=" + serial)
    ctx.obj['at'].command("&W")
    click.echo('OK')


@node.command("purge")
@click.pass_context
def node_purge(ctx):
    '''Detach all nodes'''
    ctx.obj['at'].command("$PURGE")
    ctx.obj['at'].command("&W")
    click.echo('OK')


@cli.group()
@click.pass_context
def config(ctx):
    '''Config'''
    select_device(ctx)


@config.command('channel')
@click.option('--set', 'set_channel', type=int, help='New cahnnel')
@click.pass_context
def config_channel(ctx, set_channel=None):
    '''Channel'''
    if set_channel is not None:
        if set_channel < 0 or set_channel > 20:
            raise CliException("Bad channel range")

        ctx.obj['at'].command("$CHANNEL=%d" % set_channel)
        ctx.obj['at'].command("&W")

    click.echo(ctx.obj['at'].command("$CHANNEL?")[0][1:])


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

    ctx.obj['at'].command("$KEY=%s" % key)
    ctx.obj['at'].command("&W")

    click.echo('OK')


@cli.command('info')
@click.pass_context
def info(ctx):
    select_device(ctx)
    click.echo('Model: ' + ctx.obj['at'].command("+CGMM")[0][7:])
    click.echo('ID:    ' + ctx.obj['at'].command("+CGSN")[0][7:])


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
