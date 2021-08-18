# netchat session object

import pexpect
import sys

from .exception import ParameterError
from .constant import status, spawn
from .script import Script


class Session():
    """connect to a listening TCP port and perform expect/send interaction 

    :param: address: (host, port) for TCP connection
    :type: address: tuple
    :param: script: script composed of EXPECT,SEND element pairs as string or Script
    :type: script: str/Script
    :param: wait_timeout: seconds before an EXPECT wait will return TIMEOUT, defaults to Infinite 
    :type: wait_timeout: int, optional
    :param: out: stream for writing receive data from the connection, defaults to stdout 
    :type: out: file-type, optional
    :param: err: stream for writing diagnostic and status messages, defaults to stderr
    :type: out: file-type, optional
    :param: events: a list of status events for which diagnostics should be emitted
    :type: events: netchat.status, optional
    :param: spawn_type: type of subprocess used for TCP connection (spawn.internal, spawn.socat, spawn.nc)
    :type: spawn_type: netchat.spawn

    ..note:: ``script`` can be a ``Script`` or a string

    ..note:: a chat script is composed of one or more pairs of two-word elements separated by whitespace
      in the format ``EXPECT [SEND] [EXPECT [SEND]]...``
       - elements may be exact-match strings or regular expressions
       - elements are separated by whitespace and may be quote-delimited
       - a single element is treated as an EXPECT
       - an EXPECT without a SEND will have a null SEND appended
    """

    def __init__(
        self, address, script, *, wait_timeout=None, out=sys.stdout, err=sys.stderr, events=[status.EXPECT,status.SEND], spawn_type=spawn.internal
    ):
        """constructor"""

        address, port = address

        if isinstance(script, str):
            self.script = Script(script=script)
        elif isinstance(script, Script):
            self.script = script
        else:
            raise ParameterError(f'script must be of type {str} or {Script}')

        self.wait_timeout = wait_timeout
        self.out = out
        self.err = err
        self.events = events

        if spawn_type == spawn.socat:
            self.command = f'socat stdio tcp4-connect:{address}:{port}'
        elif spawn_type == spawn.nc:
            self.command = f'nc {address} {port}'
        elif spawn_type == spawn.internal:
            self.command = f'python3 -m netchat {address}:{port} --subprocess'
        else:
            raise ParameterError(f'invalid spawn_type {spawn_type}')

    def run(self, callback=None):
        """connect to the server and iterate through the script, waiting for EXPECT and sending SEND
          :param: callback: function to be called on state change events
          :type: callback: callback_function(netchat.status, data)
          :return: EOF, TIMEOUT, or DONE 
          :rtype: netchat.state
        """
        with Handler(self.command, self.wait_timeout, self.out, self.err, self.events, callback) as handler:
            for step in self.script:
                try:
                    handler.expect(step.expect)
                    handler.send(step.send)
                except pexpect.exceptions.EOF as ex:
                    return handler.event(status.EOF)
                except pexpect.exceptions.TIMEOUT as ex:
                    return handler.event(status.TIMEOUT)
        return status.DONE


class Handler():
    """context manager for the pexpect subprocess

    :param: command: command line for the spawned subprocess
    :type: command: str
    :param: timeout: expect timeout
    :type: timeout: int
    :param: out: stream for writing connection receive data
    :type: out: file-type
    :param: err: stream for writing diagnostic messages
    :type: out: file-type
    :param: events: list of desired status change diagnostics
    :type: events: status
    :param: callback: function to be called on state change events
    :type: callback: function
    """

    def __init__(self, command, timeout, out, err, events, callback):
        self.command = command
        self.timeout = timeout
        self.out = out
        self.err = err
        self.events = events
        self.callback = callback

    def __enter__(self):
        self.event(status.CONNECTING)
        self.child = pexpect.spawn(self.command, encoding='utf-8', timeout=self.timeout, logfile=self.out, echo=False)
        self.event(status.CONNECTED)
        return self

    def __exit__(self, _, exception, traceback):
        if self.child.isalive():
            self.child.terminate()
        self.event(status.CLOSED)
        return False

    def event(self, event, data=None):
        if event in self.events:
            if self.err:
                if data:
                    self.err.write(f"{str(event)} {repr(data)}\n")
                else:
                    self.err.write(f"{str(event)}\n")
            if self.callback:
                self.callback(event, data)
        return event

    def expect(self, data):
        if data:
            self.event(status.EXPECT, data)
            ret = self.child.expect(data)
            self.event(status.FOUND, data)
        else:
            self.event(status.EXPECT_SKIPPED)

    def send(self, data):
        if data:
            self.event(status.SEND, data)
            self.child.sendline(data)
            self.event(status.SENT, data)
        else:
            self.event(status.SEND_SKIPPED)
