import unittest
from trace.tef import *
from trace.trace_analyzer import TraceAnalyzer


class TestTraceEvents(unittest.TestCase):
    def setup_tracer(self, n_events=3, n_repeat=0, prefix='event'):
        tracer = Tracer()
        ts = 0
        for _ in range(n_repeat + 1):
            for i in range(n_events):
                tracer.add_event(TraceEventDurationBegin(f'{prefix}{i:03}', ts))
                ts += 0.001
            for i in reversed(range(n_events)):
                tracer.add_event(TraceEventDurationEnd(f'{prefix}{i:03}', ts))
                ts += 0.001
        return tracer

    def test_event_name_codes_1(self):
        tracer = self.setup_tracer(n_events=1)
        trace_analyzer = TraceAnalyzer(tracer)
        self.assertDictEqual(trace_analyzer.event_name_codes, {'event000': 'A'})

    def test_event_name_codes_10(self):
        tracer = self.setup_tracer(n_events=10)
        trace_analyzer = TraceAnalyzer(tracer)
        self.assertDictEqual(
            trace_analyzer.event_name_codes,
            {
                'event000': 'A', 'event001': 'B', 'event002': 'C', 'event003': 'D', 'event004': 'E',
                'event005': 'F', 'event006': 'G', 'event007': 'H', 'event008': 'I', 'event009': 'J',
            }
        )

    def test_event_name_codes_104(self):
        tracer = self.setup_tracer(n_events=104)
        trace_analyzer = TraceAnalyzer(tracer)
        event_name_codes = trace_analyzer.event_name_codes
        self.assertEqual(event_name_codes['event000'], 'AA')
        self.assertEqual(event_name_codes['event025'], 'AZ')
        self.assertEqual(event_name_codes['event026'], 'Aa')
        self.assertEqual(event_name_codes['event051'], 'Az')
        self.assertEqual(event_name_codes['event052'], 'BA')
        self.assertEqual(event_name_codes['event103'], 'Bz')

    def test_event_string(self):
        tracer = self.setup_tracer(n_events=3)
        tracer.add_event(TraceEventInstant('event999', 1))
        trace_analyzer = TraceAnalyzer(tracer)
        self.assertEqual(trace_analyzer.events_string, 'A+B+C+C-B-A-D!')


if __name__ == '__main__':
    unittest.main()
