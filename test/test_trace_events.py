import unittest
from trace.tef import *


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

        self.assertDictEqual(event.tef,
                             {'name': 'duration-event', 'ph': 'B', 'pid': 1, 'tid': 2, 'ts': ts * 1e6, 'args': {}}
                             )

    def test_duration_end_events(self):
        ts = 124
        event = TraceEventDurationEnd('duration-event', ts)
        self.assertEqual(event.tef['ph'], 'E')
        self.assertEqual(event.tef['ts'], ts * 1e6)

    def test_instant_event(self):
        ts = 123
        event = TraceEventInstant('instant-event', ts)
        self.assertEqual(event.tef['ph'], 'i')
        self.assertIn('s', event.tef)
        self.assertEqual(event.tef['ts'], ts * 1e6)

    def test_counter_event(self):
        ts = 123
        event_name = 'counter-event'
        counter_value = 999
        event = TraceEventCounter(event_name, ts, counter_value)
        self.assertEqual(event.tef['ph'], 'C')
        self.assertDictEqual(event.tef, {**event.tef, 'args': {event_name: counter_value}})

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
        self.assertDictEqual(event.tef['args'], {'custom_attr1': 'foo', 'custom_attr2': 100})

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
        self.assertDictEqual(readback['traceEvents'][0], event1_begin.tef)
        self.assertDictEqual(readback['traceEvents'][1], event1_end.tef)
        self.assertDictEqual(readback['traceEvents'][2], event2.tef)


if __name__ == '__main__':
    unittest.main()
