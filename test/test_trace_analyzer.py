import pytest
from trazer.tef import (
    Tracer,
    TraceEventDurationBegin,
    TraceEventDurationEnd,
    TraceEventInstant,
)
from trazer.trace_analyzer import TraceAnalyzer


def setup_tracer(n_events=3, n_repeat=0, prefix='event'):
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


def setup_trace_analyzer(n_events=3, n_repeat=0, prefix='event'):
    return TraceAnalyzer(setup_tracer(n_events, n_repeat, prefix))


def test_event_name_codes_1():
    trace_analyzer = setup_trace_analyzer(n_events=1)
    assert {'event000': 'A'} == trace_analyzer.event_name_codes


def test_event_name_codes_10():
    trace_analyzer = setup_trace_analyzer(n_events=10)
    assert trace_analyzer.event_name_codes == {
        'event000': 'A',
        'event001': 'B',
        'event002': 'C',
        'event003': 'D',
        'event004': 'E',
        'event005': 'F',
        'event006': 'G',
        'event007': 'H',
        'event008': 'I',
        'event009': 'J',
    }


def test_event_name_codes_104():
    trace_analyzer = setup_trace_analyzer(n_events=104)
    event_name_codes = trace_analyzer.event_name_codes
    assert event_name_codes['event000'] == 'AA'
    assert event_name_codes['event025'] == 'AZ'
    assert event_name_codes['event026'] == 'Aa'
    assert event_name_codes['event051'] == 'Az'
    assert event_name_codes['event052'] == 'BA'
    assert event_name_codes['event103'] == 'Bz'


def test_event_string():
    tracer = setup_tracer(n_events=3)
    tracer.add_event(TraceEventInstant('event999', 1))
    trace_analyzer = TraceAnalyzer(tracer)
    assert trace_analyzer.events_string == 'A+B+C+C-B-A-D!'


def test_event_name_validation():
    trace_analyzer = setup_trace_analyzer()
    assert trace_analyzer._validate_event_name(['e', 'evt', 'event_name']) is None
    with pytest.raises(ValueError):
        trace_analyzer._validate_event_name(['event-name'])
    with pytest.raises(ValueError):
        trace_analyzer._validate_event_name(['eventname+'])
    with pytest.raises(ValueError):
        trace_analyzer._validate_event_name(['!eventname'])
    with pytest.raises(ValueError):
        trace_analyzer._validate_event_name(['*'])


def test_encode_valid_event_pattern_without_wildcard():
    trace_analyzer = setup_trace_analyzer(n_events=4)
    assert trace_analyzer._encode_event_pattern('event000+') == r'(A)\+'
    assert trace_analyzer._encode_event_pattern('event000+event001-') == r'(A)\+(B)\-'


def test_encode_valid_event_pattern_with_wildcard():
    trace_analyzer = setup_trace_analyzer(n_events=4)
    assert (
        trace_analyzer._encode_event_pattern('event000+*event003-')
        == r'(A)\+(?:(?!A\+|D\-)[a-zA-Z]{1}\W)*?(D)\-'
    )
    assert (
        trace_analyzer._encode_event_pattern('event000+event000-*event003-')
        == r'(A)\+(A)\-(?:(?!D\-)[a-zA-Z]{1}\W)*?(D)\-'
    )
    assert (
        trace_analyzer._encode_event_pattern('event000-*event003-')
        == r'(A)\-(?:(?!D\-)[a-zA-Z]{1}\W)*?(D)\-'
    )
    assert (
        trace_analyzer._encode_event_pattern('event000+event001+*event002-event003-')
        == r'(A)\+(B)\+(?:(?!A\+|B\+|C\-|D\-)[a-zA-Z]{1}\W)*?(C)\-(D)\-'
    )


def test_encode_invalid_event_pattern():
    trace_analyzer = setup_trace_analyzer(n_events=3)
    with pytest.raises(ValueError):
        trace_analyzer._encode_event_pattern('event000event111')
    with pytest.raises(ValueError):
        trace_analyzer._encode_event_pattern('event000$')
    with pytest.raises(ValueError):
        trace_analyzer._encode_event_pattern('e0+e0-')
    with pytest.raises(ValueError):
        trace_analyzer._encode_event_pattern('event000+event111')
    with pytest.raises(ValueError):
        trace_analyzer._encode_event_pattern('event000+*')


def test_map_string_index_to_event():
    trace_analyzer = setup_trace_analyzer(n_events=3)
    # events string = A+B+C+C-B-A-
    assert (
        trace_analyzer._map_string_index_to_event(0) == trace_analyzer.tracer.events[0]
    )
    assert (
        trace_analyzer._map_string_index_to_event(10) == trace_analyzer.tracer.events[5]
    )


def test_merge_events_repeat0():
    trace_analyzer = setup_trace_analyzer(n_events=3)
    trace_analyzer.merge_events('event000+*event001-', 'merged_event')
    merged_event_begin = trace_analyzer.tracer.events[-2]
    merged_event_end = trace_analyzer.tracer.events[-1]
    assert isinstance(merged_event_begin, TraceEventDurationBegin)
    assert isinstance(merged_event_end, TraceEventDurationEnd)
    assert merged_event_begin.name == 'merged_event'
    assert merged_event_end.name == 'merged_event'
    assert merged_event_begin.ts == 0
    assert merged_event_end.ts == 4000


def test_merge_events_repeat2():
    trace_analyzer = setup_trace_analyzer(n_events=3, n_repeat=2)
    tracer = trace_analyzer.tracer
    trace_analyzer.merge_events('event000+*event001-', 'merged_event')
    # 3 merged_event expected
    for e in tracer.events[-6:]:
        assert e.name == 'merged_event'
    for i, e in enumerate(tracer.events[-6::2]):
        assert isinstance(e, TraceEventDurationBegin)
        assert e.ts == pytest.approx(6000 * i)
    for i, e in enumerate(tracer.events[-5::2]):
        assert isinstance(e, TraceEventDurationEnd)
        assert e.ts == pytest.approx(4000 + 6000 * i)


def test_merge_events_repeat2_but_match_only_repetition():
    tracer = setup_tracer(n_events=3, n_repeat=2)
    tracer.add_event(TraceEventDurationBegin('final_event', 0.1))
    trace_analyzer = TraceAnalyzer(tracer)
    trace_analyzer.merge_events('event000+*event000-final_event+', 'merged_event')
    assert tracer.events[-3].name != 'merged_event'
    assert isinstance(tracer.events[-2], TraceEventDurationBegin)
    assert tracer.events[-2].name == 'merged_event'
    assert tracer.events[-2].ts == pytest.approx(12000)
    assert isinstance(tracer.events[-1], TraceEventDurationEnd)
    assert tracer.events[-1].name == 'merged_event'
    assert tracer.events[-1].ts == pytest.approx(100000)
