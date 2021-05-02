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
        self.assertDictEqual({'event000': 'A'}, trace_analyzer.event_name_codes)

    def test_event_name_codes_10(self):
        tracer = self.setup_tracer(n_events=10)
        trace_analyzer = TraceAnalyzer(tracer)
        self.assertDictEqual(
            {
                'event000': 'A', 'event001': 'B', 'event002': 'C', 'event003': 'D', 'event004': 'E',
                'event005': 'F', 'event006': 'G', 'event007': 'H', 'event008': 'I', 'event009': 'J',
            },
            trace_analyzer.event_name_codes
        )

    def test_event_name_codes_104(self):
        tracer = self.setup_tracer(n_events=104)
        trace_analyzer = TraceAnalyzer(tracer)
        event_name_codes = trace_analyzer.event_name_codes
        self.assertEqual('AA', event_name_codes['event000'])
        self.assertEqual('AZ', event_name_codes['event025'])
        self.assertEqual('Aa', event_name_codes['event026'])
        self.assertEqual('Az', event_name_codes['event051'])
        self.assertEqual('BA', event_name_codes['event052'])
        self.assertEqual('Bz', event_name_codes['event103'])

    def test_event_string(self):
        tracer = self.setup_tracer(n_events=3)
        tracer.add_event(TraceEventInstant('event999', 1))
        trace_analyzer = TraceAnalyzer(tracer)
        self.assertEqual('A+B+C+C-B-A-D!', trace_analyzer.events_string)

    def test_event_name_validation(self):
        tracer = Tracer()
        trace_analyzer = TraceAnalyzer(tracer)
        self.assertIsNone(trace_analyzer._validate_event_name(['e', 'evt', 'event_name']))
        with self.assertRaises(ValueError):
            trace_analyzer._validate_event_name(['event-name'])
        with self.assertRaises(ValueError):
            trace_analyzer._validate_event_name(['eventname+'])
        with self.assertRaises(ValueError):
            trace_analyzer._validate_event_name(['!eventname'])
        with self.assertRaises(ValueError):
            trace_analyzer._validate_event_name(['*'])

    def test_encode_valid_event_pattern(self):
        tracer = self.setup_tracer(n_events=3)
        trace_analyzer = TraceAnalyzer(tracer)
        self.assertEqual('A+', trace_analyzer._encode_event_pattern('event000+'))
        self.assertEqual('A+B-', trace_analyzer._encode_event_pattern('event000+event001-'))
        self.assertEqual(r'A+([a-zA-Z]{1}\W)*C-', trace_analyzer._encode_event_pattern('event000+*event002-'))
        self.assertEqual(r'A+([a-zA-Z]{1}\W)*', trace_analyzer._encode_event_pattern('event000+*'))

    def test_encode_invalid_event_pattern(self):
        tracer = self.setup_tracer(n_events=3)
        trace_analyzer = TraceAnalyzer(tracer)
        with self.assertRaises(ValueError):
            trace_analyzer._encode_event_pattern('event000event111')
        with self.assertRaises(ValueError):
            trace_analyzer._encode_event_pattern('event000$')
        with self.assertRaises(ValueError):
            trace_analyzer._encode_event_pattern('e0+e0-')
        with self.assertRaises(ValueError):
            trace_analyzer._encode_event_pattern('event000+event111')


if __name__ == '__main__':
    unittest.main()
