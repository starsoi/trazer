from typing import Any, Dict, Type, Union
from trazer.trace import Trace, TraceEvent
import trazer.trace as trace


_TEF_MANDATORY_PROPS: Dict[Type[TraceEvent], Dict[str, Any]] = {
    trace.TraceEvent: {},
    trace.TraceEventDurationBegin: {'ph': 'B'},
    trace.TraceEventDurationEnd: {'ph': 'E'},
    trace.TraceEventCounter: {'ph': 'C'},
    trace.TraceEventInstant: {'ph': 'i', 's': 'g'},
}


def to_tef(trace_or_event: Union[Trace, TraceEvent]) -> Dict[str, Any]:
    """Export the trace to a dict corresponding to the Trace Event Format JSON.
    (see https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview)

    :param trace_or_event: A complete trace or an individual trace event to be exported.
    :return: A dict in Trace Event Format.
    """

    if isinstance(trace_or_event, Trace):
        return {
            'traceEvents': [e.tef for e in trace_or_event.events],
            'displayTimeUnit': 'ms',
        }
    elif isinstance(trace_or_event, TraceEvent):
        tef_dict = {
            k: v
            for k, v in {
                **trace_or_event.__dict__,
                **trace_or_event.__class__.__dict__,
                **_TEF_MANDATORY_PROPS[trace_or_event.__class__],
            }.items()
            if not k.startswith('_') and k != 'tef'
        }
        tef_dict['ts'] *= 1e3  # timestamp in tef is in micro-seconds
        return tef_dict
    else:
        raise NotImplementedError
