from __future__ import annotations
from functools import wraps
from typing import IO, List, Iterable, Optional
from abc import ABC


class Trace(object):
    """A ``Trace`` contains all collected trace events and can be exported into different trace file formats for
    further processing in other tools, e.g. for visualization.
    """

    def __init__(self):
        """Initialize a ``Trace`` instance with the following properties:

        * ``events``: A list of trace events, which has the insertion order of the contained trace events.
        """
        self.events: List[TraceEvent] = []

    def add_event(self, event: TraceEvent):
        """Add a trace event into the trace.

        :param event: The event instance to be appended.
        :return: None
        """
        self.events.append(event)

    def add_events(self, events: Iterable[TraceEvent]):
        """Add trace events from an iterable into the trace.

        :param events: An iterable providing trace events.
        :return: None
        """
        for event in events:
            self.add_event(event)

    def to_tef_json(self, file_like: Optional[IO[str]] = None) -> Optional[str]:
        """Get the JSON in Trace Event Format
        The string can be written into a JSON file for the visualization in Chrome ```chrome://tracing```.

        :param file_like: A file-like object for writing the JSON.
        :return: The JSON string or None if ``file_path`` is provided.
        """
        import trazer.export as export

        return export.to_tef_json(self, file_like=file_like)

    def __str__(self):
        """Get the string representation of a trace.
        :return: The string representation of each events per line.
        """
        return "\n".join(str(event) for event in self.events)


class TraceEvent(ABC):
    """An abstract class containing the basic properties for a trace event."""

    def __init__(self, name: str, ts: float, pid: int = 0, tid: int = 0, **kwargs):
        """Initialize a trace event.

        :param name: Name of the event. It shall be unique in the trace.
        :param ts: Timestamp of the event in milliseconds.
        :param pid: Process ID of the event (for execution trace).
        :param tid: Thread ID of the event (for execution trace).
        :param kwargs: Other attributes to be associated with the event.
        """
        self.name = name
        self.ts = ts
        self.pid = pid
        self.tid = tid
        self.args = kwargs

    @property
    def tef(self):
        """Get a dict containing the properties required for the Trace Event Format.

        :return: A dict with properties from Trace Event Format
        """
        import trazer.export as export

        return export.to_tef_event_dict(self)

    def __str__(self):
        """Get the string representation of this event.
        It has a format: ``[<timestamp>]: <name of the event> (shortname of the event)``

        :return: The string representation.
        """
        return f'[{self.ts} ms]: {self.name} ({self._shortname})'

    def __repr__(self):
        return str(self)


class TraceEventDurationBegin(TraceEvent):
    """A ``TraceEvent`` representing the beginning of an event with certain duration.
    The complete span of an event with certain duration is defined by its corresponding ``TraceEventDurationBegin``
    and ``TraceEventDurationEnd``
    """

    _shortname = 'B'


class TraceEventDurationEnd(TraceEvent):
    """A ``TraceEvent`` representing the end of an event with certain duration.
    The complete span of an event with certain duration is defined by its corresponding ``TraceEventDurationBegin``
    and ``TraceEventDurationEnd``
    """

    _shortname = 'E'


class TraceEventCounter(TraceEvent):
    """A ``TraceEvent`` representing a utility event containing a counter which changes with time."""

    _shortname = 'C'

    def __init__(self, name, ts, value, pid=0, tid=0):
        super().__init__(name, ts, pid, tid)
        self.args.update({name: value})


class TraceEventInstant(TraceEvent):
    """A ``TraceEvent`` representing an instantaneous event without any duration."""

    _shortname = 'I'


def _validate_property_access(func):
    """Validate the access to the properties of EventChain."""

    @wraps(func)
    def _func(event_chain: EventChain):
        if len(event_chain.events) == 0:
            raise AttributeError(
                f'EventChain "{event_chain.name}" is empty. Property {func.__name__} does not have value.'
            )
        return func(event_chain)

    return _func


class EventChain(Trace):
    """An event chain consists of a set of related events. It is basically a subset of a trace."""

    def __init__(self, name: str):
        """Initialize an event chain.

        :param name: The name of the event chain.
        """
        self.name = name
        super().__init__()

    @property
    @_validate_property_access
    def ts(self) -> float:
        """Get the timestamp of the beginning of the event chain.

        :return: The timestamp of the first event in the event chain.
        """
        return self.events[0].ts

    @property
    @_validate_property_access
    def dur(self) -> float:
        """Get the duration of the event chain.

        :return: The time difference between the last and the first event in the event chain.
        """
        return self.events[-1].ts - self.events[0].ts

    @property
    @_validate_property_access
    def begin_event(self) -> TraceEvent:
        """Get the first event in the event chain.

        :return: The first event.
        """
        return self.events[0]

    @property
    @_validate_property_access
    def end_event(self) -> TraceEvent:
        """Get the last event in the event chain.
        :return: The last event.
        """
        return self.events[-1]

    def __str__(self):
        return f'[{self.begin_event.ts} - {self.end_event.ts} ms]: {self.name} ({len(self.events)} events)'

    def __repr__(self):
        return str(self)

    def as_event_pair(self):
        """Represent the even chain as a pair of (TraceEventDurationBegin, TraceEventDurationEnd)
        The events in the event pair have the same name as the event chain.
        The two events has the timestamps of the begin and end events respectively.

        :return: The event pair.
        """
        begin_event = TraceEventDurationBegin(self.name, self.begin_event.ts)
        end_event = TraceEventDurationEnd(self.name, self.end_event.ts)
        return begin_event, end_event
