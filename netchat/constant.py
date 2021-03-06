# netchat session object

import enum


class State(enum.IntEnum):

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


status = State(
    'status', 'CONNECTING CONNECTED CLOSED DONE EXPECT EXPECT_SKIPPED FOUND SEND SEND_SKIPPED SENT EOF TIMEOUT'
)

spawn = State('SPAWN', 'internal socat nc')
