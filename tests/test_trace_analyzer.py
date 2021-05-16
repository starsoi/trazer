import pytest
from trazer.trace import (
    Trace,
    TraceEventDurationBegin,
    TraceEventDurationEnd,
    TraceEventInstant,
)
from trazer.analyzer import TraceAnalyzer


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
    trace = setup_trace(n_events=3)
    trace.add_event(TraceEventInstant('event999', 1))
    trace_analyzer = TraceAnalyzer(trace)
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
        trace_analyzer._map_string_index_to_event(0) == trace_analyzer.trace.events[0]
    )
    assert (
        trace_analyzer._map_string_index_to_event(10) == trace_analyzer.trace.events[5]
    )


def test_merge_events_repeat0():
    trace_analyzer = setup_trace_analyzer(n_events=3)
    trace_analyzer.merge_events('event000+*event001-', 'merged_event')
    merged_event_begin = trace_analyzer.analyzer_trace.events[-2]
    merged_event_end = trace_analyzer.analyzer_trace.events[-1]
    assert isinstance(merged_event_begin, TraceEventDurationBegin)
    assert isinstance(merged_event_end, TraceEventDurationEnd)
    assert merged_event_begin.name == 'merged_event'
    assert merged_event_end.name == 'merged_event'
    assert merged_event_begin.ts == 0
    assert merged_event_end.ts == 4


def test_merge_events_repeat2():
    trace_analyzer = setup_trace_analyzer(n_events=3, n_repeat=2)
    analyzer_trace = trace_analyzer.merge_events('event000+*event001-', 'merged_event')
    # 3 merged_event expected
    for e in analyzer_trace.events[-6:]:
        assert e.name == 'merged_event'
    for i, e in enumerate(analyzer_trace.events[-6::2]):
        assert isinstance(e, TraceEventDurationBegin)
        assert e.ts == pytest.approx(6 * i)
    for i, e in enumerate(analyzer_trace.events[-5::2]):
        assert isinstance(e, TraceEventDurationEnd)
        assert e.ts == pytest.approx(4 + 6 * i)


def test_merge_events_repeat2_but_match_only_repetition():
    trace = setup_trace(n_events=3, n_repeat=2)
    trace.add_event(TraceEventDurationBegin('final_event', 100))
    trace_analyzer = TraceAnalyzer(trace)
    analyzer_trace = trace_analyzer.merge_events(
        'event000+*event000-final_event+', 'merged_event'
    )
    assert len(analyzer_trace.events) == 2
    assert isinstance(analyzer_trace.events[-2], TraceEventDurationBegin)
    assert analyzer_trace.events[-2].name == 'merged_event'
    assert analyzer_trace.events[-2].ts == pytest.approx(12)
    assert isinstance(analyzer_trace.events[-1], TraceEventDurationEnd)
    assert analyzer_trace.events[-1].name == 'merged_event'
    assert analyzer_trace.events[-1].ts == pytest.approx(100)


def test_export_merged_trace_to_tef_json():
    trace_analyzer = setup_trace_analyzer(n_repeat=1)
    trace_analyzer.merge_events('event000+*event000-', 'merged_event')
    exported_tef_json = trace_analyzer.to_tef_json(1000)

    expected_trace = trace_analyzer.trace
    expected_trace.add_event(TraceEventDurationBegin('merged_event', 0, pid=1000))
    expected_trace.add_event(TraceEventDurationEnd('merged_event', 5, pid=1000))
    expected_trace.add_event(TraceEventDurationBegin('merged_event', 6, pid=1000))
    expected_trace.add_event(TraceEventDurationEnd('merged_event', 11, pid=1000))

    assert exported_tef_json == expected_trace.tef_json
