"""Test the Trigger class."""

from mcb import Trigger


def f(a, b):
    pass


def test_init():
    t = Trigger('test', f)
    assert t.regexp == 'test'
    assert t.func is f
    assert t.priority == 0
    assert t.classes == ()
    assert t.kwarg_names == []
