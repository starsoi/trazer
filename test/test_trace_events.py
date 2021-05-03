import unittest
from trazer.tef import *


class TestTraceEvents(unittest.TestCase):
    def test_trace_event_base_tef(self):
        event = TraceEvent('event-name', 1.23, pid=1, tid=2, attr='foo')
        self.assertDictEqual(event.tef,
                             {'name': 'event-name', 'pid': 1, 'tid': 2, 'ts': 1.23 * 1e6, 'args': {'attr': 'foo'}}
                             )

    def test_duration_begin_events(self):
        ts = 123
        event = TraceEventDurationBegin('duration-event', ts)
        self.assertEqual(event.tef['ph'], 'B')
        self.assertEqual(event.tef['ts'], ts * 1e6)

        event.pid = 1
        event.tid = 2

        self.assertDictEqual({'name': 'duration-event', 'ph': 'B', 'pid': 1, 'tid': 2, 'ts': ts * 1e6, 'args': {}},
                             event.tef,
                             )

    def test_duration_end_events(self):
        ts = 124
        event = TraceEventDurationEnd('duration-event', ts)
        self.assertEqual('E', event.tef['ph'])
        self.assertEqual(ts * 1e6, event.tef['ts'])

    def test_instant_event(self):
        ts = 123
        event = TraceEventInstant('instant-event', ts)
        self.assertEqual('i', event.tef['ph'])
        self.assertIn('s', event.tef)
        self.assertEqual(ts * 1e6, event.tef['ts'])

    def test_counter_event(self):
        ts = 123
        event_name = 'counter-event'
        counter_value = 999
        event = TraceEventCounter(event_name, ts, counter_value)
        self.assertEqual('C', event.tef['ph'])
        self.assertDictEqual({**event.tef, 'args': {event_name: counter_value}}, event.tef)

    def test_event_sequence(self):
        tracer = Tracer()
        event1_begin = TraceEventDurationBegin('event1', 123)
        event1_end = TraceEventDurationEnd('event1', 124)
        event2 = TraceEventInstant('event2', 123.5)

        tracer.add_event(event1_begin)
        tracer.add_event(event1_end)
        tracer.add_event(event2)

        self.assertIs(tracer.events[0], event1_begin)
        self.assertIs(tracer.events[1], event1_end)
        self.assertIs(tracer.events[2], event2)

    def test_custom_attributes(self):
        event = TraceEventDurationEnd('event', 0, custom_attr1='foo', custom_attr2=100)
        self.assertDictEqual({'custom_attr1': 'foo', 'custom_attr2': 100}, event.tef['args'])

    def test_json_export(self):
        import json
        tracer = Tracer()
        event1_begin = TraceEventDurationBegin('event1', 0.001)
        event1_end = TraceEventDurationEnd('event1', 0.002)
        event2 = TraceEventInstant('event2', 0.003)

        tracer.add_event(event1_begin)
        tracer.add_event(event1_end)
        tracer.add_event(event2)

        readback = json.loads(tracer.json)
        self.assertDictEqual(event1_begin.tef, readback['traceEvents'][0])
        self.assertDictEqual(event1_end.tef, readback['traceEvents'][1])
        self.assertDictEqual(event2.tef, readback['traceEvents'][2])


if __name__ == '__main__':
    unittest.main()
