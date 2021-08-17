import pytest
import netchat


def test_netchat():
    nc = netchat.NetChat(address='localhost', port='2222', script='howdy')
    assert nc
