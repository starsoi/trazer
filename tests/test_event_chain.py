import pytest
from trazer.trace import EventChain


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
