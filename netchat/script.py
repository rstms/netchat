# netchat script objects

import shlex
from pathlib import Path


class Element():
    """EXPECT,SEND script element

    :param: expect: data or regex to be awaited
    :type: expect: str
    :param: send: data sent after the expected data is recieved
    :type: expect: str
    """

    def __init__(self, expect, send):
        self.expect = expect
        self.send = send

    def __str__(self):
        return repr(dict(expect=self.expect, send=self.send))

    def __repr__(self):
        return f"Element<{str(self)}>"


class Script():
    """a chat script composed of EXPECT,SEND pairs

    :param: script: input string to be parsed
    :type: script: str, optional
    :param: pathname: pathname of script file
    :type: pathname: str, optional
    :param: file: readable stream for reading script
    :type: file: file-type object, optional

    ::note:
      Uses ``shlex`` to parse, so shell quoting may be used.
      Missing elements will be give a NULL value
      Any lines beginning with # will be ignored.
     
    ::note:
      EXPECT elements may be regular expressions
    """

    def __init__(self, *, script=None, pathname=None, file=None):
        self.elements = []
        if script:
            self.parse_string(script)
        elif pathname:
            self.parse_pathname(pathname)
        elif file:
            self.parse_file(file)

    def parse_string(self, script):
        """parse the input into a list of expect/send pairs

        :param: script: input string to be parsed
        :type: script: str 
        :return: script object
        :rtype: netchat.Script
        
        """
        self.elements = []
        tokens = list(shlex.shlex(script, posix=True))
        if len(tokens) & 1:
            tokens.append('')
        tokens.reverse()
        while len(tokens):
            send = tokens.pop()
            expect = tokens.pop()
            self.elements.append(Element(send, expect))

        return self

    def read_file(self, file):
        """read script from a file, ignoring comment lines

        :param: file: open file for reading script data
        :type: file: file-type
        :return: script data 
        :rtype: str
        """
        buffer = ''
        for line in file.readlines():
            line = line.strip()
            if not line.startswith('#'):
                buffer += ' ' + line
        return buffer

    def parse_file(self, file):
        """read script data from an open file and parse it
    
        :param: script_file: readable stream for reading script
        :type: script_file: file-type object, optional
        :return: script
        :rtype: netchat.Script
        """
        with file:
            return self.parse_string(read_script_file(file))

    def parse_pathname(self, pathname):
        """open and read a script file and parse the script data

        :param: pathname: pathname of script file
        :type: pathname: str
        :return: script
        :rtype: netchat.Script
        """
        with Path(pathname).open('r') as fp:
            return self.parse_file(fp)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.elements):
            ret = self.elements[self.index]
            self.index += 1
            return ret
        else:
            raise StopIteration

    def __len__(self):
        return len(self.elements)
