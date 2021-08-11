#!/usr/bin/env python3

import click
import socket
import sys
import time
from pathlib import Path

DEFAULT_TIMEOUT=10

class TimeoutError(Exception):
    pass

class ParameterError(Exception):
    pass

class Step():
    def __init__(self, line):
        line = line.strip()
        if line:
            self.send, self.expect = line.split(',')[0:2]

class Script():
    def __init__(self, input_file=None, trigger=None):
        if input_file:
            self.steps = [Step(line) for line in input_file.readlines() if (line.strip() and not line.startswith('#'))]
        elif trigger:
            self.steps = [Step(f",{trigger}")]
        else:
            raise ParameterError('Either input_file or trigger must be provided.')

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
    def __init__(self, address, port, script_file=None, trigger=None):
        self.address = address
        self.port = port
        self.script = Script(script_file, trigger)

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.address, self.port)
        click.echo(f"Connecting to {server_address}...", err=True, nl=False)
        self.sock.connect(server_address)
        click.echo("<connected>", err=True)
        return self

    def __exit__(self, _, exc, tb):
        self.sock.close()
        click.echo("\n<closed>", err=True)
        return False

    def getline(self, timeout):
        rxbuf = ''
        while(rxbuf[-1:] != '\n'):
            rxbuf+=self.sock.recv(1).decode()
            if timeout and (time.time() > timeout):
                fail('Timeout')
        rxbuf=rxbuf.strip()
        click.echo(f"--RX-->'{rxbuf}'", err=True)
        return rxbuf

    def putline(self, txbuf):
        click.echo(f"<-TX--'{txbuf}'", err=True, nl=False)
        if txbuf:
            self.sock.sendall((txbuf+'\n').encode())

@click.command(name='netchat')
@click.argument('address', type=str)
@click.argument('port', type=int)
@click.option('-s', '--script', type=click.File('r'))
@click.option('-t', '--trigger', type=str)
@click.option('-T', '--timeout', type=int, default=DEFAULT_TIMEOUT)
def netchat(address, port, script, trigger, timeout):
    if timeout:
        timeout+=time.time()
    with Handler(address, port, script, trigger) as handler:
        for step in handler.script:
            handler.putline(step.send)
            if step.expect:
                click.echo(f"  Expecting '{step.expect}'", err=True)
                while not handler.getline(timeout).startswith(step.expect): 
                    pass
            click.echo('OK', err=True)

if __name__=='__main__':
    netchat()
