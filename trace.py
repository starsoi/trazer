import json

class Tracer(object):
    def __init__(self):
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    @property
    def tef(self):
        return {
            'traceEvents': [e.tef for e in self.events],
            'displayTimeUnit': 'ms'
        }

    @property
    def json(self):
        return json.dumps(self.tef, indent=4)


class TraceEvent(object):
    def __init__(self, name, ts, pid=0, tid=0):
        self.name = name
        self.ts = ts * 1e6  # unit in trace event format is micro-second
        self.pid = pid
        self.tid = tid
        self.args = {}

    @property
    def tef(self):
        return {'name': self.name,
                'ph': self._ph,
                'ts': self.ts,
                'pid': self.pid,
                'tid': self.tid,
                'args': self.args
                }


class TraceEventDurationBegin(TraceEvent):
    _ph = 'B'


class TraceEventDurationEnd(TraceEvent):
    _ph = 'E'


class TraceEventCounter(TraceEvent):
    _ph = 'C'

    def __init__(self, name, ts, value, pid=0, tid=0):
        super().__init__(name, ts, pid, tid)
        self.args.update({name: value})
