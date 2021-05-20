from trazer import (
    Trace,
    TraceEventDurationBegin,
    TraceEventDurationEnd,
    TraceEventCounter,
    TraceEventInstant,
)
from trazer.trace import TraceEvent


def test_trace_event_base_tef():
    event = TraceEvent('event-name', 1.23, pid=1, tid=2, attr='foo')
    assert event.tef == {
        'name': 'event-name',
        'pid': 1,
        'tid': 2,
        'ts': 1.23 * 1e3,
        'args': {'attr': 'foo'},
    }


def test_duration_begin_events():
    ts = 123
    event = TraceEventDurationBegin('duration-event', ts)
    assert event.tef['ph'] == 'B'
    assert event.tef['ts'] == ts * 1e3

    event.pid = 1
    event.tid = 2

    assert event.tef == {
        'name': 'duration-event',
        'ph': 'B',
        'pid': 1,
        'tid': 2,
        'ts': ts * 1e3,
        'args': {},
    }


def test_duration_end_events():
    ts = 124
    event = TraceEventDurationEnd('duration-event', ts)
    assert event.tef['ph'] == 'E'
    assert event.tef['ts'] == ts * 1e3


def test_instant_event():
    ts = 123
    event = TraceEventInstant('instant-event', ts)
    assert event.tef['ph'] == 'i'
    assert 's' in event.tef
    assert event.tef['ts'] == ts * 1e3


def test_counter_event():
    ts = 123
    event_name = 'counter-event'
    counter_value = 999
    event = TraceEventCounter(event_name, ts, counter_value)
    assert event.tef['ph'] == 'C'
    assert event.tef == {**event.tef, 'args': {event_name: counter_value}}


def test_add_event_individually():
    trace = Trace()
    event1_begin = TraceEventDurationBegin('event1', 123)
    event1_end = TraceEventDurationEnd('event1', 124)
    event2 = TraceEventInstant('event2', 123.5)

    trace.add_event(event1_begin)
    trace.add_event(event1_end)
    trace.add_event(event2)

    assert trace.events[0] is event1_begin
    assert trace.events[1] is event1_end
    assert trace.events[2] is event2


def test_add_events_from_iterable():
    trace = Trace()
    events = [
        TraceEventDurationBegin('event1', 123),
        TraceEventDurationEnd('event1', 124),
        TraceEventInstant('event2', 123.5),
    ]
    trace.add_events(events)

    assert trace.events[0] == events[0]
    assert trace.events[1] == events[1]
    assert trace.events[2] == events[2]

    events = [
        TraceEventDurationBegin('event1', 1230),
        TraceEventDurationEnd('event1', 1240),
        TraceEventInstant('event2', 1235),
    ]
    trace.add_events(e for e in events)

    assert trace.events[3] == events[0]
    assert trace.events[4] == events[1]
    assert trace.events[5] == events[2]


def test_custom_attributes():
    event = TraceEventDurationEnd('event', 0, custom_attr1='foo', custom_attr2=100)
    assert event.tef['args'] == {'custom_attr1': 'foo', 'custom_attr2': 100}


def test_json_export():
    import json
    import tempfile

    trace = Trace()
    event1_begin = TraceEventDurationBegin('event1', 0.001)
    event1_end = TraceEventDurationEnd('event1', 0.002)
    event2 = TraceEventInstant('event2', 0.003)

    trace.add_event(event1_begin)
    trace.add_event(event1_end)
    trace.add_event(event2)

    with tempfile.TemporaryFile('w+t') as tmp:
        trace.to_tef_json(tmp)
        tmp.seek(0)
        readback = json.load(tmp)
    assert readback['traceEvents'][0] == event1_begin.tef
    assert readback['traceEvents'][1] == event1_end.tef
    assert readback['traceEvents'][2] == event2.tef
