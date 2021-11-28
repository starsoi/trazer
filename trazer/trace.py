from __future__ import annotations
from functools import wraps
from typing import Any, Dict, IO, List, Iterable, Tuple, Optional
from abc import ABC


class Trace(object):
    """A ``Trace`` contains all collected trace events and can be exported into different trace file formats for
    further processing in other tools, e.g. for visualization.
    """

    def __init__(self):
        """Initialize a ``Trace`` instance with the following properties:

        * ``events``: A list of trace events, which has the insertion order of the contained trace events.
        * ``process_name``: Mapping from process id to process name
        * ``thread_name``: Mapping from the pair of (process id, thread id) to thread name
        * ``flow_ids``: Mapping from the flow name to flow id
        """
        self.events: List[TraceEvent] = []
        self.process_names: Dict[int, str] = {}
        self.thread_names: Dict[Tuple[int, int], str] = {}
        self.flow_ids: Dict[str, int] = {}

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

    def set_process_name(self, pid: int, name: str):
        """Set the process name for the process identified by `pid`.

        :param pid: Process id.
        :param name: Process name.
        :return: None
        """
        self.process_names[pid] = name

    def set_thread_name(self, pid: int, tid: int, name: str):
        """Set the thread name for the thread identified by `pid` and `tid`.

        :param pid: Process id.
        :param tid: Thread id.
        :param name: Thread name.
        :return: None
        """
        self.thread_names[(pid, tid)] = name

    @property
    def metadata_events(self) -> List[TraceEventMetadata]:
        """Get a list of metadata events for the trace.
        It contains the metadata events for process and thread names.

        :return: A list of `TraceEventMetadata`.
        """
        p_metadata = [
            TraceEventMetadata('process_name', pid=pid, name=p_name)
            for pid, p_name in self.process_names.items()
        ]
        t_metadata = [
            TraceEventMetadata('thread_name', pid=pid, tid=tid, name=t_name)
            for (pid, tid), t_name in self.thread_names.items()
        ]
        return p_metadata + t_metadata

    def add_flow(
        self, name: str, src: TraceEventDurationBegin, dest: TraceEventDurationBegin
    ):
        """Add a flow from one duration to another.
        It is a little bit tricky to derive the timestamps for the flow events.
        The start and end points of the flow need to be bound to "slices",
        i.e. the duration bars in the trace visualization.
        The exact slice to be bound to is determined by the timestamp of the respective flow event.

        The general rule is:
        - The start point is bound to the most recent enclosing slice, if multiple slices cover the start timestamp.
        - The end point is bound to the next slice that begins, which is closest to the end timestamp.

        For Perfetto v20.1, the end timestamp needs to be strictly smaller than the slice to be bound to.

        :param name: The name of the flow.
        :param src: The begin of the source duration.
        :param dest: The begin of the destination duration.
        :return: None
        """
        flow_id = self.flow_ids.setdefault(
            name, len(self.flow_ids)
        )  # Simple counter-based generation of flow id.
        flow_event_start = TraceEventFlowStart(name, src.ts, flow_id)

        # Make the timestamp of the flow end tiny bit earlier than that of the destination duration.
        flow_event_end = TraceEventFlowEnd(name, dest.ts - 1e-9, flow_id)
        self.add_event(flow_event_start)
        self.add_event(flow_event_end)

    def to_tef_json(
        self, file_like: Optional[IO[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the JSON in Trace Event Format
        The string can be written into a JSON file for the visualization in Chrome ```chrome://tracing```.

        :param file_like: A file-like object for writing the JSON.
        :return: The JSON dict or None if ``file_path`` is provided.
        """
        import trazer.export as export

        return export.to_tef_json(self, file_like=file_like)

    def __str__(self):  # pragma: no cover
        """Get the string representation of a trace.
        :return: The string representation of each events per line.
        """
        return "\n".join(str(event) for event in self.events)


class TraceEvent(ABC):
    """An abstract class containing the basic properties for a trace event."""

    def __init__(
        self,
        event_name: str,
        ts: Optional[float] = None,
        pid: Optional[int] = None,
        tid: Optional[int] = None,
        **kwargs,
    ):
        """Initialize a trace event.

        :param event_name: Name of the event. It shall be unique in the trace.
        :param ts: Timestamp of the event in seconds.
        :param pid: Process ID of the event (for execution trace).
        :param tid: Thread ID of the event (for execution trace).
        :param kwargs: Other attributes to be associated with the event.
        """
        self.name = event_name
        if ts is not None:
            self.ts = ts
        if pid is not None:
            self.pid = pid
        if tid is not None:
            self.tid = tid
        self.args = kwargs

    @property
    def tef(self):
        """Get a dict containing the properties required for the Trace Event Format.

        :return: A dict with properties from Trace Event Format
        """
        import trazer.export as export

        return export.to_tef_event_dict(self)

    def __str__(self):  # pragma: no cover
        """Get the string representation of this event.
        It has a format: ``[<timestamp>]: <name of the event> (shortname of the event)``

        :return: The string representation.
        """
        return f'[{self.ts} ms]: {self.name} ({self._shortname})'

    def __repr__(self):  # pragma: no cover
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


class TraceEventMetadata(TraceEvent):
    """A ``TraceEvent`` representing a metadata event for associating extra information with the events in the trace."""

    _shortname = 'M'

    def __init__(
        self,
        metadata_name: str,
        *,
        pid: Optional[int] = None,
        tid: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(metadata_name, pid=pid, tid=tid, **kwargs)


class TraceEventFlowStart(TraceEvent):
    """A ``TraceEvent`` representing the start of a flow."""

    _shortname = 's'

    def __init__(self, name: str, ts: float, id_: int, **kwargs):
        super().__init__(name, ts, **kwargs)
        self.id = id_


class TraceEventFlowEnd(TraceEvent):
    """A ``TraceEvent`` representing the end of a flow."""

    _shortname = 'f'

    def __init__(self, name: str, ts: float, id_: int, **kwargs):
        super().__init__(name, ts, **kwargs)
        self.id = id_


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

    def __str__(self):  # pragma: no cover
        return f'[{self.begin_event.ts} - {self.end_event.ts} ms]: {self.name} ({len(self.events)} events)'

    def __repr__(self):  # pragma: no cover
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
