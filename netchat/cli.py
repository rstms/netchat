#!/usr/bin/env python3

import click
import sys

from netchat import Session, Script, spawn, status, ParameterError, Connection


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
@click.option('-c', '--callback', is_flag=True, help='use callback mechanism')
@click.option('-q', '--quiet', is_flag=True, help='suppress diagnostics')
@click.option('-v', '--verbose', is_flag=True, help='increase diagnostic detail')
@click.option('-d', '--debug', is_flag=True, help='output python stack trace on exceptions')
@click.option('--subprocess', is_flag=True, hidden=True)
def cli(address, script, file, timeout, spawn_type, echo, callback, quiet, verbose, debug, subprocess):

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

    if isinstance(address, str):
        if ':' in address:
            address = address.split(':')
        else:
            raise ParameterError('address must include ":port"')

    address, port = address[:2]
    port = int(port)

    if subprocess:
        breakpoint()
        sys.exit(Connection((address, port), debug).run())

    if bool(script) and bool(file):
        raise ParameterError('cannot specify both SCRIPT and --file option')

    if script:
        script = Script(script=script)
    elif file:
        script = Script(file=file)

    def _callback(event, data):
        click.echo(f"CALLBACK {str(event)}: {repr(data)}", err=True)

    if echo:
        output = sys.stdout
    else:
        output = None

    if callback:
        callback = _callback

    if quiet:
        error = None
    else:
        error = sys.stderr

    if verbose:
        events = list(status.__members__.values())
    else:
        events=[status.EXPECT, status.SEND]

    spawn_type = spawn[spawn_type]

    Session((address, port), script, wait_timeout=timeout, out=output, err=error, events=events, spawn_type=spawn_type).run(callback)


if __name__ == '__main__':
    cli()
