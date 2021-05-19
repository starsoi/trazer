import pytest
from trazer import EventChain, TraceEventDurationBegin, TraceEventDurationEnd


@pytest.fixture
def basic_event_chain():
    event_chain = EventChain('event_chain')
    event_chain.add_events(
        (
            TraceEventDurationBegin('event', 0),
            TraceEventDurationEnd('event', 1),
            TraceEventDurationBegin('event', 2),
            TraceEventDurationEnd('event', 3),
        )
    )
    return event_chain


def test_empty_event_chain():
    event_chain = EventChain('event_chain')
    with pytest.raises(AttributeError):
        print(event_chain.ts)
    with pytest.raises(AttributeError):
        print(event_chain.dur)
    with pytest.raises(AttributeError):
        print(event_chain.begin_event)
    with pytest.raises(AttributeError):
        print(event_chain.end_event)


def test_event_chain_to_event_pair(basic_event_chain):
    begin_event, end_event = basic_event_chain.as_event_pair()
    assert begin_event.name == 'event_chain'
    assert begin_event.ts == 0
    assert end_event.name == 'event_chain'
    assert end_event.ts == 3


def test_event_chain_properties(basic_event_chain):
    assert basic_event_chain.ts == 0
    assert basic_event_chain.dur == 3
