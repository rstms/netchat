#!/usr/bin/env python3

import click
import sys

from netchat import Session, Script, spawn, ParameterError, Connector


@click.command(name='netchat')
@click.version_option()
@click.argument('address', type=str)
@click.argument('script', type=str, required=False, default=None)
@click.option('-f', '--file', type=click.File('r'), help='chat script file')
@click.option('-t', '--timeout', type=int, default=None, help='timeout for each WAIT element')
@click.option(
    '-s',
    '--spawn-type',
    type=click.Choice(['internal', 'socat', 'nc']),
    default='internal',
    show_default=True,
    help='connection program'
)
@click.option('-e', '--echo', is_flag=True, help='write receive data to stdout')
@click.option('-q', '--quiet', is_flag=True, help='suppress diagnostics')
@click.option('-v', '--verbose', is_flag=True, help='increase diagnostic detail')
@click.option('-d', '--debug', is_flag=True, help='output python stack trace on exceptions')
@click.option('--subprocess', is_flag=True, hidden=True)
def cli(address, script, file, timeout, spawn_type, echo, quiet, verbose, debug, subprocess):

    def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
        if debug:
            debug_hook(exception_type, exception, traceback)
        else:
            if verbose:
                message = str(exception)
            else:
                message = str(exception).split('\n')[0]
            click.echo(f"{exception_type}.{message}", err=True)
            sys.exit(-1)

    sys.excepthook = exception_handler

    if subprocess:
        sys.exit(Connector(address, debug).run())

    if isinstance(address, str):
        if ':' in address:
            address = address.split(':')
        else:
            raise ParameterError('address must include ":port"')

    address, port = address[:2]
    port = int(port)

    if bool(script) and bool(file):
        raise ParameterError('cannot specify both SCRIPT and --file option')

    if script:
        script = Script(script=script)
    elif file:
        script = Script(file=file)

    def _callback(event, data):
        if verbose:
            click.echo(f"CALLBACK {str(event)}: {repr(data)}", err=True)
        else:
            click.echo(str(event), err=True)

    if echo:
        output = sys.stdout
    else:
        output = None

    error = sys.stderr

    callback = _callback

    if quiet:
        output = None
        error = None
        callback = None

    spawn_type = spawn[spawn_type]

    Session((address, port), script, wait_timeout=timeout, out=output, err=error, spawn_type=spawn_type).run(callback)


if __name__ == '__main__':
    cli()
