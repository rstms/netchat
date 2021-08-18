# netchat exception classes


class Error(Exception):
    pass


class TimeoutError(Error):
    pass


class ParameterError(Error):
    pass
