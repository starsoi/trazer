import pytest

from tests.utils import setup_trace, setup_trace_analyzer
from trazer import (
    Trace,
    TraceEventDurationBegin,
    TraceEventDurationEnd,
    TraceEventInstant,
)
from trazer import TraceAnalyzer
from trazer.analyzer import _EventNameNotFoundError


def test_analyzer_with_empty_trace():
    trace = Trace()
    trace_analyzer = TraceAnalyzer(trace)
    assert trace_analyzer.match('test+', 'test') == []
    assert trace_analyzer.to_tef_json(100) == {
        'traceEvents': [],
        'displayTimeUnit': 'ms',
    }


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
        trace_analyzer._encode_event_pattern('event000-*event003+event003-event003-')
        == r'(A)\-(?:(?!D\-)[a-zA-Z]{1}\W)*?(D)\+(D)\-(D)\-'
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
    with pytest.raises(_EventNameNotFoundError):
        trace_analyzer._encode_event_pattern('e0+e0-')
    with pytest.raises(ValueError):
        trace_analyzer._encode_event_pattern('event000+event111')
    with pytest.raises(ValueError):
        trace_analyzer._encode_event_pattern('event000+*')


def test_map_string_index_to_event():
    trace_analyzer = setup_trace_analyzer(n_events=3)
    # events string = A+B+C+C-B-A-
    assert trace_analyzer._map_string_index_to_event(0) == (
        0,
        trace_analyzer.trace.events[0],
    )
    assert trace_analyzer._map_string_index_to_event(10) == (
        5,
        trace_analyzer.trace.events[5],
    )


def test_match_events_repeat0():
    trace_analyzer = setup_trace_analyzer(n_events=3)
    trace_analyzer.match('event000+*event001-', 'event_chain')
    assert trace_analyzer.event_chains[0].name == 'event_chain'
    assert trace_analyzer.event_chains[0].events == trace_analyzer.trace.events[0:5]


def test_match_events_repeat2():
    trace_analyzer = setup_trace_analyzer(n_events=3, n_repeat=2)
    trace_analyzer.match('event000+*event001-', 'event_chain')

    # 3 event_chain expected
    assert len(trace_analyzer.event_chains) == 3

    for e in trace_analyzer.event_chains:
        assert e.name == 'event_chain'

    event_chains = trace_analyzer.event_chains

    assert event_chains[0].events == trace_analyzer.trace.events[0:5]
    assert event_chains[1].events == trace_analyzer.trace.events[6:11]
    assert event_chains[2].events == trace_analyzer.trace.events[12:17]


def test_match_events_repeat2_only_last_repetition_matched():
    trace = setup_trace(n_events=3, n_repeat=2)
    trace.add_event(TraceEventDurationBegin('final_event', 100))
    trace_analyzer = TraceAnalyzer(trace)
    event_chains = trace_analyzer.match(
        'event000+*event000-final_event+', 'event_chain'
    )
    assert len(event_chains) == 1
    assert event_chains[0].events == trace.events[12:19]


def test_match_events_repeat1_wildcard_without_exclusion():
    trace = setup_trace(n_events=3, n_repeat=1)
    trace.add_event(TraceEventDurationBegin('final_event', 100))
    trace_analyzer = TraceAnalyzer(trace)
    event_chains = trace_analyzer.match(
        'event000+*event000-final_event+', 'event_chain', False
    )  # The whole trace is expected to be matched
    assert len(event_chains) == 1
    assert event_chains[0].events == trace.events


def test_match_same_pattern_multiple_times():
    trace_analyzer = setup_trace_analyzer()
    trace_analyzer.match('event000+*event000-', 'merged_event')
    trace_analyzer.match('event000+*event000-', 'merged_event')
    trace_analyzer.match('event000+*event000-', 'merged_event_new')

    assert len(trace_analyzer.event_chains) == 1
    assert trace_analyzer.event_chains[0].name == 'merged_event_new'
    assert trace_analyzer.event_chains[0].begin_event == trace_analyzer.trace.events[0]
    assert trace_analyzer.event_chains[0].end_event == trace_analyzer.trace.events[-1]


def test_match_multiple_event_patterns():
    trace_analyzer = setup_trace_analyzer(n_repeat=1)
    trace_events = trace_analyzer.trace.events

    match_result1 = trace_analyzer.match('event000+*event000-', 'merged_event1')
    assert len(match_result1) == 2
    assert match_result1[0].events == trace_events[0:6]
    assert match_result1[1].events == trace_events[6:12]

    match_result2 = trace_analyzer.match('event001+*event001-', 'merged_event2')
    assert len(match_result2) == 2
    assert match_result2[0].events == trace_events[1:5]
    assert match_result2[1].events == trace_events[7:11]

    match_result3 = trace_analyzer.match('event000+*event000-', 'merged_event1_new')
    assert len(match_result3) == 2
    assert match_result3[0].name == 'merged_event1_new'
    assert match_result3[0].events == trace_events[0:6]
    assert match_result3[1].name == 'merged_event1_new'
    assert match_result3[1].events == trace_events[6:12]

    assert len(trace_analyzer.event_chains) == 4
    assert trace_analyzer.event_chains[0].name == 'merged_event1_new'
    assert trace_analyzer.event_chains[0].events == trace_events[0:6]
    assert trace_analyzer.event_chains[1].name == 'merged_event2'
    assert trace_analyzer.event_chains[2].name == 'merged_event1_new'
    assert trace_analyzer.event_chains[2].events == trace_events[6:12]
    assert trace_analyzer.event_chains[3].name == 'merged_event2'


def test_export_merged_trace_to_tef_json():
    trace_analyzer = setup_trace_analyzer(n_repeat=1)
    trace_analyzer.match('event000+*event000-', 'merged_event')
    exported_tef_json = trace_analyzer.to_tef_json(1000)

    expected_trace = setup_trace(n_repeat=1)
    expected_trace.add_event(TraceEventDurationBegin('merged_event', 0, pid=1000))
    expected_trace.add_event(TraceEventDurationEnd('merged_event', 5, pid=1000))
    expected_trace.add_event(TraceEventDurationBegin('merged_event', 6, pid=1000))
    expected_trace.add_event(TraceEventDurationEnd('merged_event', 11, pid=1000))

    assert expected_trace.to_tef_json() == exported_tef_json

    # Export to file
    import json
    import tempfile

    tmp = tempfile.TemporaryFile('w+t')
    trace_analyzer.to_tef_json(1000, tmp)
    tmp.seek(0)
    assert expected_trace.to_tef_json() == json.load(tmp)
    tmp.close()
