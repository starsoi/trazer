import pytest

from trazer import (
    Trace,
    TraceEventDurationBegin,
    TraceEventDurationEnd,
    TraceEventCounter,
    TraceEventInstant,
    TraceEventMetadata,
    TraceEventFlowStart,
    TraceEventFlowEnd,
)
from trazer.trace import TraceEvent
from trazer.export import to_tef_event_dict
from tests.utils import setup_trace


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

    trace.set_thread_name(0, 0, 'test thread')

    with tempfile.TemporaryFile('w+t') as tmp:
        trace.to_tef_json(tmp)
        tmp.seek(0)
        readback = json.load(tmp)
    assert readback['traceEvents'][0] == event1_begin.tef
    assert readback['traceEvents'][1] == event1_end.tef
    assert readback['traceEvents'][2] == event2.tef
    assert readback['traceEvents'][3] == trace.metadata_events[0].tef


def test_metadata_event():
    event_process = TraceEventMetadata('process_name', pid=123, name='test process')
    event_thread = TraceEventMetadata(
        'thread_name', pid=456, tid=1000, name='test thread'
    )
    with pytest.raises(TypeError):
        # For pid and tid, keyword arguments must be used
        TraceEventMetadata('process_name', 123, 456, name='test process')

    process_tef = event_process.tef
    assert process_tef['ph'] == 'M'
    assert process_tef['pid'] == 123
    assert 'tid' not in process_tef
    assert process_tef['args']['name'] == 'test process'

    thread_tef = event_thread.tef
    assert thread_tef['ph'] == 'M'
    assert thread_tef['pid'] == 456
    assert thread_tef['tid'] == 1000
    assert thread_tef['args']['name'] == 'test thread'


def test_set_process_name():
    trace = Trace()
    event1_begin = TraceEventDurationBegin('event1', 0.001, pid=100, tid=0)
    event1_end = TraceEventDurationEnd('event1', 0.005, pid=100, tid=0)
    event2_begin = TraceEventDurationBegin('event2', 0.002, pid=200, tid=100)
    event2_end = TraceEventDurationEnd('event2', 0.004, pid=200, tid=100)
    trace.add_events((event1_begin, event1_end, event2_begin, event2_end))
    trace.set_process_name(100, 'process1')
    trace.set_process_name(200, 'process2')
    trace.set_thread_name(100, 0, 'process1_thread')
    trace.set_thread_name(200, 100, 'process2_thread')

    metadata_events = trace.metadata_events
    assert len(metadata_events) == 4
    for event in metadata_events:
        assert event.name in ['process_name', 'thread_name']
        if event.name == 'process_name':
            assert event.pid in [100, 200]
            if event.pid == 100:
                assert event.args == {'name': 'process1'}
            if event.pid == 200:
                assert event.args == {'name': 'process2'}
        if event.name == 'thread_name':
            assert (event.pid, event.tid) in [(100, 0), (200, 100)]
            if (event.pid, event.tid) == (100, 0):
                assert event.args == {'name': 'process1_thread'}
            if (event.pid, event.tid) == (200, 100):
                assert event.args == {'name': 'process2_thread'}


def test_time_unit_conversion():
    event = TraceEventDurationEnd('event1', 1)
    assert to_tef_event_dict(event)['ts'] == 1000
    assert to_tef_event_dict(event, 'ms')['ts'] == 1e3
    assert to_tef_event_dict(event, 'us')['ts'] == 1e6
    assert to_tef_event_dict(event, 'ns')['ts'] == 1e9


def test_flow_event():
    """This test needs to be verified manually in Perfetto
    Expected flows:
    - From 1st event000 to 2nd event001
    - From 1st event001 to 2nd event000
    - From 1st event001 to 2nd event001
    """
    event_start = TraceEventFlowStart('flow', 123, 100)
    event_end = TraceEventFlowEnd('flow', 456, 100)
    assert event_start.tef['ph'] == 's'
    assert event_end.tef['ph'] == 'f'
    assert event_start.tef['id'] == 100
    assert event_end.tef['id'] == 100

    trace = setup_trace(n_repeat=3)
    trace.add_flow('flow1', trace.events[1], trace.events[6])
    trace.add_flow('flow2', trace.events[1], trace.events[7])
    trace.add_flow('flow3', trace.events[0], trace.events[7])

    trace.set_process_name(0, 'test process')
    trace.set_thread_name(0, 0, 'test thread')

    trace.to_tef_json(open('test.json', 'w'))
