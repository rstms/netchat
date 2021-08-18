# netchat object tests

import pytest
import logging

from pprint import pprint as pp
from pathlib import Path

from netchat import Session


def p(label, msg):
    pp({label: msg})


def test_init():
    nc = Session(('localhost', 2222), script='howdy')
    assert nc


def test_wait_quiet(server):
    # connect and wait for 'the'
    nc = Session(('localhost', server.port), script='the', out=None, err=None)
    ret = nc.run()


def test_wait_output(server, callback):
    # connect and wait for 'the'
    # catch diagnostic output

    nc = Session(('localhost', server.port), script='the', out=None, err=None)

    ret = nc.run(callback.rx)
    assert len(callback.buffer), 'expected diagnostic output'
    p('output', callback.buffer)


def test_wait_output_and_file(server, callback):
    # connect and wait for 'the'
    # catch diagnostic output
    # catch server output

    writer = Path('/tmp') / 'log_text'
    with writer.open('w') as ofp:
        nc = Session(('localhost', server.port), script='the', out=ofp, err=None)
        ret = nc.run(callback.rx)

    p('running', server.running())
    p('elapsed', server.elapsed())

    assert len(callback.buffer), 'diagnostic output should be present'
    p('output', callback.buffer)

    reader = Path('/tmp') / 'log_text'
    log_text = reader.read_text()

    assert len(log_text), 'server output should be present'
    p('log_text', log_text)

    p('server_stdout', server.stdout)
    p('server_stderr', server.stderr)


def test_send_and_receive_script(server, callback):
    # use a bidirectional script
    # catch diagnostic output
    # catch server output

    script = "any 'level one' when 'level two' 'who' 'level three'"

    writer = Path('/tmp') / 'log_text'
    with writer.open('w') as ofp:
        nc = Session(('localhost', server.port), script=script, out=ofp, err=None)
        ret = nc.run(callback.rx)

    p('running', server.running())
    p('elapsed', server.elapsed())

    assert len(callback.buffer), 'diagnostic output should be present'
    p('output', callback.buffer)

    reader = Path('/tmp') / 'log_text'
    log_text = reader.read_text()

    assert len(log_text), 'server output should be present'
    p('log_text', log_text)

    p('server_stdout', server.stdout)
    p('server_stderr', server.stderr)
