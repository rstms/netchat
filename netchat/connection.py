# netchat connector

import logging
import socket
import sys
import termios

from collections import deque
from select import select

BUFSIZ=1024

class Connection():
    def __init__(self, address, debug=False):
        self.address = address
        if debug:
            logging.info('setting debug mode')
            level=logging.DEBUG
        else:
            level=logging.INFO
        logging.basicConfig(level=level)
        logging.debug('debug')

    def no_run(self):
        logging.info('munging terminal settings')
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)

        new[3] = new[3] & ~(termios.ECHO | termios.ICANON) # lflags
        new[6][termios.VMIN] = 0  # cc
        new[6][termios.VTIME] = 0 # cc

        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, new)
            self._run()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            logging.info('un-munging terminal settings')

    def run(self):
        logging.info('run')
        logging.debug('run')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #sock.setblocking(False)
        logging.info(f"Connecting to {self.address}")
        sock.connect(self.address)
        logging.info("<connected>")

        rx_buf = deque()
        tx_buf = deque()

        stdin = sys.stdin.buffer
        stdout = sys.stdout.buffer

        readable = [sock, stdin]
        active = [sock,stdin, stdout]

        done = False

        while not done:
            logging.debug(f'start: tx={len(tx_buf)} rx={len(rx_buf)}')

            writeable = []
            if len(rx_buf):
                writeable.append(stdout)
            if len(tx_buf):
                writeable.append(sock)
        
            sources, sinks, errors = select(readable, writeable, active)
            logging.debug(f'{len(sources)} {len(sinks)} {len(errors)}')

            if sock in sinks:
                data = tx_buf.popleft()
                logging.debug(f'<--tx_buf {len(tx_buf)}')
                logging.debug('-->socket {repr(data)}')
                sock.sendall(data)

            if stdout in sinks:
                data = rx_buf.popleft()
                logging.debug(f'<--rx_buf {len(rx_buf)}')
                logging.debug(f'-->stdout {repr(data)}')
                stdout.write(data)

            if sock in sources:
                logging.debug('socket.recv')
                data = sock.recv(BUFSIZ)
                logging.debug(f'<--socket {repr(data)}')
                rx_buf.append(data)
                logging.debug(f'rx_buf<-- {len(rx_buf)}')

            if stdin in sources:
                logging.debug('stdin.read')
                data = stdin.read(BUFSIZ)
                logging.debug(f'<--stdin {len(data)} {repr(data)}')
                tx_buf.append(data)
                logging.debug(f'tx_buf<-- {len(tx_buf)}')

            if errors:
                raise RuntimeError(f'socket exception: {repr(errors)}')

        sock.close()
        logging.info("<closed>")
