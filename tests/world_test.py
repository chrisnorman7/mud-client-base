"""Test the World class."""

import re
from pytest import raises
from mcb import Trigger, World, dont_abort

_extra = 'Testing stuff.'
patterns = ('test', 'this', 'stuff')


class BuildArgsWorks(Exception):
    pass


class CustomWorld(World):
    def build_args(self, trigger, match, extra):
        assert extra is _extra
        raise BuildArgsWorks()


class TriggerWorkedException(Exception):
    pass


class TriggerFailedException(Exception):
    pass


def f0():
    """Don't raise an exception, just work."""


def f1():
    raise TriggerWorkedException()


def f2(name, age=None):
    assert name == 'Peter'
    assert int(age) == 42
    raise TriggerWorkedException()


def f3():
    raise TriggerFailedException()


def test_init():
    w = World()
    assert w.trigger_class is Trigger
    assert w.classes == []
    assert w.active_triggers == []
    assert w.inactive_triggers == []


def test_trigger():
    w = World()
    t = w.trigger('test')(f1)
    assert isinstance(t, Trigger)
    assert t.regexp.pattern == 'test'
    assert t.func is f1
    assert t == Trigger(re.compile('test'), f1)


def test_custom_trigger():
    w = World()
    t = w.trigger('test', classes=('test',))(f2)
    assert t.func is f2
    assert t.classes == ('test',)
    assert t == Trigger(re.compile('test'), f2, classes=('test',))


def test_is_active():
    w = World()
    t = w.trigger('test')(f1)
    assert w.is_active(t)
    t.classes = ('inactive',)
    w.classes.append('test')
    assert not w.is_active(t)
    w.classes.clear()
    assert not w.is_active(t)


def test_sort_key():
    w = World()
    with raises(AttributeError):
        w.sorted_key(w)
    t = w.trigger('test')(f1)
    assert w.sorted_key(t) is t.priority


def test_activate_trigger():
    w = World()
    t = w.trigger('test', classes=('inactive', 'classes'))(f1)
    assert t in w.inactive_triggers
    assert t not in w.active_triggers
    w.activate_trigger(t)
    assert t in w.active_triggers
    assert t not in w.inactive_triggers


def test_activate_triggers():
    w = World()
    triggers = []
    length = len(patterns)
    for pattern in patterns:
        triggers.append(
            w.trigger(
                pattern,
                classes=('inactive',)
            )(f1)
        )
    assert length is len(triggers)
    assert not w.active_triggers
    assert len(w.inactive_triggers) is length
    w.activate_triggers(triggers)
    assert len(w.active_triggers) is length
    assert not w.inactive_triggers


def test_deactivate_triggers():
    w = World()
    triggers = []
    for pattern in patterns:
        triggers.append(
            w.trigger(
                pattern
            )(f1)
        )
    assert len(triggers) is len(patterns)
    length = len(triggers)
    assert not w.inactive_triggers
    assert len(w.active_triggers) is length
    w.deactivate_triggers(triggers)
    assert not w.active_triggers
    assert len(w.inactive_triggers) is length


def test_enable_classes():
    w = World()
    class_name = 'inactive'
    triggers = []
    for pattern in patterns:
        triggers.append(w.trigger(pattern, classes=(class_name,))(f1))
    assert not w.active_triggers
    assert len(w.inactive_triggers) is len(patterns)
    w.enable_classes(class_name)
    assert not w.inactive_triggers
    assert len(w.active_triggers) is len(patterns)


def test_disable_classes():
    class_name = 'inactive'
    w = World()
    w.enable_classes(class_name)
    triggers = []
    for pattern in patterns:
        triggers.append(w.trigger(pattern, classes=(class_name,))(f1))
    assert not w.inactive_triggers
    assert len(w.active_triggers) is len(patterns)
    w.disable_classes(class_name)
    assert not w.active_triggers
    assert len(w.inactive_triggers) is len(patterns)


def test_handle_line_no_triggers():
    w = World()
    w.handle_line('test')


def test_handle_line_no_arguments():
    w = World()
    w.trigger('test')(f1)
    with raises(TriggerWorkedException):
        w.handle_line('test')


def test_handle_line_arguments():
    w = World()
    w.trigger(
        '^My name is ([^ ]+) and my age is ([0-9]+).$'
    )(f2)
    with raises(TriggerWorkedException):
        w.handle_line('My name is Peter and my age is 42.')


def test_handle_line_no_matches():
    w = World()
    w.trigger('test1')(f1)
    w.trigger('test2')(f1)
    w.handle_line('This is a test which fails.')


def test_handle_line_multiple_classes():
    w = World()
    w.trigger('^fail$', classes=('inactive',))(f1)
    w.trigger('^succeed$')(f1)
    w.handle_line('fail')
    with raises(TriggerWorkedException):
        w.handle_line('succeed')


def test_handle_line_multiple_triggers():
    results = []
    w = World()

    @w.trigger('^test$')
    def test1():
        results.append('hello')

    @w.trigger('^test$')
    def test2():
        results.append('world')

    w.handle_line('test')
    assert results == ['hello']


def test_handle_line_dont_abort():
    results = []
    w = World()
    pattern = '^test ([^$]+)$'

    def f(text):
        results.append(text)
        dont_abort()

    for x in range(2):
        w.trigger(pattern)(f)
    w.handle_line('test this')
    assert results == ['this', 'this']
    w.trigger(pattern)(results.append)
    w.trigger(pattern)(results.append)
    results.clear()
    w.handle_line('test test')
    assert results == ['test', 'test', 'test']


def test_handle_line_priority():
    w = World()
    line = 'test'
    w.trigger(line)(f3)
    w.trigger(line, priority=-1)(f1)
    with raises(TriggerWorkedException):
        w.handle_line(line)


def test_build_args():
    w = CustomWorld()
    w.handle_line('No triggers to match.')
    w.trigger('^test$')(f1)
    with raises(BuildArgsWorks):
        w.handle_line('test', _extra)


def test_number_single():
    w = World()
    w.trigger('^test$')(f0)
    w.trigger('^this$')(f0)
    assert w.handle_line('test') == 1
    assert w.handle_line('this') == 1
    w.trigger('test', priority=-1)(dont_abort)  # Make sure it's first.
    assert w.handle_line('test') == 2
