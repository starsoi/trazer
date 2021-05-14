from __future__ import annotations
from typing import List
from abc import ABC
import json


class Tracer(object):
    def __init__(self):
        self.events: List[TraceEvent] = []

    def add_event(self, event: TraceEvent):
        self.events.append(event)

    @property
    def tef(self):
        return {'traceEvents': [e.tef for e in self.events], 'displayTimeUnit': 'ms'}

    @property
    def json(self):
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
        return {
            k: v
            for k, v in {**self.__dict__, **self.__class__.__dict__}.items()
            if not k.startswith('_') and k != 'tef'
        }

    def __str__(self):
        return f'[{self.ts} us]: {self.name} ({self.ph})'

    def __repr__(self):
        return str(self)


class TraceEventDurationBegin(TraceEvent):
    ph = 'B'


class TraceEventDurationEnd(TraceEvent):
    ph = 'E'


class TraceEventCounter(TraceEvent):
    ph = 'C'

    def __init__(self, name, ts, value, pid=0, tid=0):
        super().__init__(name, ts, pid, tid)
        self.args.update({name: value})


class TraceEventInstant(TraceEvent):
    ph = 'i'
    s = 'g'
