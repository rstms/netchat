#!/usr/bin/env python3

import click
import socket
import sys
import time
import shlex
from pathlib import Path
import pexpect

DEFAULT_TIMEOUT=10

class TimeoutError(Exception):
    pass

class ParameterError(Exception):
    pass

class Step():
    def __init__(self, expect, send):
        self.expect=expect
        self.send=send

    def __str__(self):
        return repr(dict(expect=self.expect,send=self.send))

    def __repr__(self):
        return f"Step({str(self)})"

class Script():
    def __init__(self, input_file=None, input_string=None):
        self.steps = []
        if input_file:
            input_string = ''
            for line in input_file.readlines():
                line=line.strip()
                if not line.startswith('#'):
                    input_string += ' ' + line
        elif not input_string:
            raise ParameterError('Either input_file or trigger must be provided.')

        tokens = list(shlex.shlex(input_string, posix=True))
        if len(tokens) & 1: 
            tokens.append('')
        tokens.reverse()
        while len(tokens):
            send = tokens.pop()
            expect = tokens.pop()
            self.steps.append(Step(send, expect))

    def __iter__(self):
        self.index = 0
        return self 

    def __next__(self):
        if self.index < len(self.steps):
            ret = self.steps[self.index]
            self.index += 1
            return ret
        else:
            raise StopIteration

def fail(error):
    click.echo(f"Error: {error}", err=True)
    raise click.Abort()

class Handler():
    def __init__(self, *, address, port, script_file=None, script_string=None, echo=False):
        self.address = address
        self.port = port
        self.script = Script(script_file, script_string)
        self.echo = echo

    def __enter__(self):
        self.child = pexpect.spawn(f'socat stdio tcp4-connect:{self.address}:{self.port}')
        if self.echo:
            self.child.logfile_read = sys.stdout
        return self

    def __exit__(self, _, exc, tb):
        if self.child.isalive():
            self.child.terminate(force=True)
        return False

    def send(self, data):
        return self.child.sendline(data)

    def expect(self, data):
        return self.child.expect(data)

@click.command(name='netchat')
@click.argument('address', type=str)
@click.argument('port', type=int)
@click.argument('script', type=str, required=False, default=None)
@click.option('-f', '--file', type=click.File('r'))
@click.option('-t', '--timeout', type=int, default=DEFAULT_TIMEOUT)
@click.option('-v', '--verbose', is_flag=True)
@click.option('-e', '--echo', is_flag=True)
@click.option('-d', '--debug', is_flag=True)
def netchat(address, port, script, file, timeout, verbose, echo, debug):

    def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
        if debug:
            debug_hook(exception_type, exception, traceback)
        else:
            click.echo(f"{exception_type.__name__}: {exception}")
            sys.exit(0)
    sys.excepthook = exception_handler

    if timeout:
        timeout+=time.time()
    with Handler(address=address, port=port, script_file=file, script_string=script, echo=echo) as handler:
        for step in handler.script:
            if step.expect:
                if verbose:
                    click.echo(f"Waiting for '{step.expect}'...", nl=False, err=True)
                handler.expect(step.expect)
            if step.send:
                if verbose:
                    click.echo(f"Sending '{step.send}'", err=True)
                handler.send(step.send)
    if verbose:
        click.echo("Terminated", err=True)

if __name__=='__main__':
    netchat()
