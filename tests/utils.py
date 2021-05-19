from trazer import Trace, TraceEventDurationBegin, TraceEventDurationEnd, TraceAnalyzer


def setup_trace(n_events=3, n_repeat=0, prefix='event'):
    trace = Trace()
    ts = 0
    for _ in range(n_repeat + 1):
        for i in range(n_events):
            trace.add_event(TraceEventDurationBegin(f'{prefix}{i:03}', ts))
            ts += 1
        for i in reversed(range(n_events)):
            trace.add_event(TraceEventDurationEnd(f'{prefix}{i:03}', ts))
            ts += 1
    return trace


def setup_trace_analyzer(n_events=3, n_repeat=0, prefix='event'):
    return TraceAnalyzer(setup_trace(n_events, n_repeat, prefix))
