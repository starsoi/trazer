from __future__ import annotations
from typing import List
from abc import ABC
import json


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

    @property
    def tef(self):
        """Get a dict containing the properties required for the Trace Event Format.

        :return: A dict with properties from Trace Event Format
        """
        import trazer.export as export

        return export.to_tef(self)

    @property
    def tef_json(self):
        """Get the JSON string of ``Trace.tef``.
        The string can be written into a JSON file for the visualization in Chrome ```chrome://tracing```.

        :return: The JSON string.
        """
        return json.dumps(self.tef, indent=4)


class TraceEvent(ABC):
    """An abstract class containing the basic properties for a trace event."""

    def __init__(self, name: str, ts: float, pid: int = 0, tid: int = 0, **kwargs):
        self.name = name
        self._ts = ts  # original input timestamp in seconds
        self.ts = ts * 1e6  # unit in trazer event format is micro-second
        self.pid = pid
        self.tid = tid
        self.args = kwargs

    @property
    def tef(self):
        """Get a dict containing the properties required for the Trace Event Format.

        :return: A dict with properties from Trace Event Format
        """
        import trazer.export as export

        return export.to_tef(self)

    def __str__(self):
        """Get the string representation of this event.
        It has a format: ``[<timestamp>]: <name of the event> (shortname of the event)``

        :return: The string representation.
        """
        return f'[{self.ts} us]: {self.name} ({self._shortname})'

    def __repr__(self):
        return str(self)


class TraceEventDurationBegin(TraceEvent):
    _shortname = 'B'


class TraceEventDurationEnd(TraceEvent):
    _shortname = 'E'


class TraceEventCounter(TraceEvent):
    _shortname = 'C'

    def __init__(self, name, ts, value, pid=0, tid=0):
        super().__init__(name, ts, pid, tid)
        self.args.update({name: value})


class TraceEventInstant(TraceEvent):
    _shortname = 'I'
