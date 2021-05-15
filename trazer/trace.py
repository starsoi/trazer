from __future__ import annotations
from typing import List
from abc import ABC
import json


class Trace(object):
    def __init__(self):
        self.events: List[TraceEvent] = []

    def add_event(self, event: TraceEvent):
        self.events.append(event)

    @property
    def tef(self):
        import trazer.export as export

        return export.to_tef(self)

    @property
    def tef_json(self):
        return json.dumps(self.tef, indent=4)


class TraceEvent(ABC):
    def __init__(self, name: str, ts: float, pid: int = 0, tid: int = 0, **kwargs):
        self.name = name
        self._ts = ts  # original input timestamp in seconds
        self.ts = ts * 1e6  # unit in trazer event format is micro-second
        self.pid = pid
        self.tid = tid
        self.args = kwargs

    @property
    def tef(self):
        import trazer.export as export

        return export.to_tef(self)

    def __str__(self):
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
