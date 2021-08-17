# netchat object tests

import pytest
import logging

from pprint import pprint as pp
from pathlib import Path

from netchat import NetChat


def p(label, msg):
    pp({label: msg})


def test_init():
    nc = NetChat(address='localhost', port='2222', script='howdy')
    assert nc


def test_wait_quiet(server):
    # connect and wait for 'the'
    nc = NetChat(address='localhost', port=server.port, script='the')
    ret = nc.run()


def test_wait_output(server):
    # connect and wait for 'the'
    # catch diagnostic output

    buf = []

    def outfunc(message):
        logging.info(message)
        buf.append(message)

    nc = NetChat(address='localhost', port=server.port, script='the', output_function=outfunc)
    ret = nc.run()
    assert len(buf), 'expected diagnostic output'
    p('output', buf)


def test_wait_output_and_file(server):
    # connect and wait for 'the'
    # catch diagnostic output
    # catch server output

    buf = []

    def outfunc(message):
        logging.info(message)
        buf.append(message)

    writer = Path('/tmp') / 'log_text'
    with writer.open('w') as ofp:
        nc = NetChat(address='localhost', port=server.port, script='the', output_function=outfunc, log_file=ofp)
        ret = nc.run()

    p('running', server.running())
    p('elapsed', server.elapsed())

    assert len(buf), 'diagnostic output should be present'
    p('output', buf)

    reader = Path('/tmp') / 'log_text'
    log_text = reader.read_text()

    assert len(log_text), 'server output should be present'
    p('log_text', log_text)

    p('server_stdout', server.stdout)
    p('server_stderr', server.stderr)


def test_send_and_receive_script(server):
    # use a bidirectional script
    # catch diagnostic output
    # catch server output

    buf = []

    def outfunc(message):
        logging.info(message)
        buf.append(message)

    script = "any 'level one' when 'level two' 'who' 'level three'"

    writer = Path('/tmp') / 'log_text'
    with writer.open('w') as ofp:
        nc = NetChat(address='localhost', port=server.port, script=script, output_function=outfunc, log_file=ofp)
        ret = nc.run()

    p('running', server.running())
    p('elapsed', server.elapsed())

    assert len(buf), 'diagnostic output should be present'
    p('output', buf)

    reader = Path('/tmp') / 'log_text'
    log_text = reader.read_text()

    assert len(log_text), 'server output should be present'
    p('log_text', log_text)

    p('server_stdout', server.stdout)
    p('server_stderr', server.stderr)
