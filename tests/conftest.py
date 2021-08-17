import pytest
import subprocess
import logging
from time import time


class Server():

    def __init__(self, port=2000, count=300, delay=1):
        logging.info(f'{self} init')
        self.port = port
        self.count = count
        self.delay = delay
        self.started = None
        self.stopped = None
        self.stdout = ''
        self.stderr = ''
        self.command = [
            'socat',
            '-d',
            '-d',
            '-d',
            '-v',
            f'tcp4-listen:{port},reuseaddr,fork',
            f"system:'for s in $(seq {count}); do fortune -a; sleep {delay}; done'",
        ]

    def __enter__(self):
        logging.info(f'{self} enter')
        self.started = time()
        self.process = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return self

    def __exit__(self, _, exception, traceback):
        logging.info(f'{self} exit')
        self.ret = self.process.poll()
        if not self.ret:
            self.kill()
        self.stopped = time()
        return False

    def read(self, timeout=None):
        logging.info(f'{self} read')
        if self.running():
            stdout, stderr = self.process.communicate(None, timeout)
            if stdout:
                logging.info(f'{self} stdout {stdout}')
            if stderr:
                logging.info(f'{self} stdout {stdout}')
            self.stdout += stdout
            self.stderr += stderr
        return self.stdout, self.stderr

    def stop(self, timeout=None):
        logging.info(f'{self} stop')
        self.ret = self.process.poll()
        if not self.ret:
            self.process.terminate()
            self.ret = self.process.wait(timeout)
        if not self.stopped:
            self.stopped = time()

    def kill(self):
        logging.info(f'{self} kill')
        self.ret = self.process.poll()
        if not self.ret:
            self.process.kill()
        if not self.stopped:
            self.stopped = time()

    def running(self):
        ret = self.process.poll()
        return not ret

    def elapsed(self):
        if self.stopped:
            end = self.stopped()
        else:
            end = time()
        return end - self.started


@pytest.fixture(scope='session')
def server():
    logging.info('session server setup')
    with Server() as s:
        yield s
    logging.info('session server teardown')
