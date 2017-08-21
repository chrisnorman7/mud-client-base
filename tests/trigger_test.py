"""Test the Trigger class."""

from mcb import Trigger


def test_init():
    t = Trigger('test', print)
    assert t.regexp == 'test'
    assert t.func is print
    assert t.priority is 0
    assert t.classes == ()
