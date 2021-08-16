#!/usr/bin/env python3

import click
import io
import os
import shlex
import socket
import sys
import time

from pathlib import Path
from pexpect import spawn, fdpexpect

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

class ScriptFile():
    def __init__(self, input_file):
        self.buffer = ''
        for line in input_file.readlines():
            line=line.strip()
            if not line.startswith('#'):
                self.buffer += ' ' + line

    def __str__(self):
        return self.buffer
        
class Script():
    def __init__(self, input_string=None):
        self.steps = []
        if not input:
            raise ParameterError('Missing required script string')

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

class Handler():
    def __init__(self, command, script, timeout, output_function, log_file):
        self.command = command
        self.script = Script(script)
        self.timeout = timeout
        self.outfunc = output_function 
        self.log = log_file

    def __enter__(self):
        self.output('Connecting...')
        self.child = spawn(self.command, encoding='utf-8', timeout=self.timeout, logfile=self.log)
        self.output('Connected.')
        return self

    def __exit__(self, _, exception, traceback):
        if self.child.isalive():
            self.child.terminate()
        self.output('Terminated.')
        return False

    def output(self, message):
        if self.outfunc:
            self.outfunc(message)

    def send(self, data):
        if data:
            self.output(f"Sending '{data}'")
            self.child.sendline(data)

    def expect(self, data):
        if data:
            self.output(f"Waiting for '{data}'...")
            self.child.expect(data)
            self.output(f"Received '{data}'.")

def click_output(message):
    click.echo(message, err=True)

class NetChat():
    def __init__(self, *, address, port, script, timeout=None, output_function=None, log_file=None):
        command = f'socat stdio tcp4-connect:{address}:{port}' 
        self.handler = Handler(command, script, timeout, output_function, log_file)

    def run(self):
        with self.handler as h:
            for step in h.script:
                h.expect(step.expect)
                h.send(step.send)

@click.command(name='netchat')
@click.version_option()
@click.argument('address', type=str)
@click.argument('port', type=int)
@click.argument('script', type=str, required=False, default=None)
@click.option('-f', '--file', type=click.File('r'))
@click.option('-t', '--timeout', type=int, default=None)
@click.option('-v', '--verbose', is_flag=True)
@click.option('-e', '--echo', is_flag=True)
@click.option('-d', '--debug', is_flag=True)
def netchat(address, port, script, file, timeout, verbose, echo, debug):

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

    if file:
        script = str(ScriptFile(file))

    if verbose:
        output = click_output
    else:
        output = None

    if echo:
        log = sys.stdout
    else:
        log = None

    NetChat(address=address, port=port, script=script, timeout=timeout, output_function=output, log_file=log).run()


if __name__=='__main__':
    netchat()

