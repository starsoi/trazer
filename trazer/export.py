from typing import Any, Dict, List, Type, Union
from trazer import Trace
import trazer.trace as trace
from trazer.trace import TraceEvent


_TEF_MANDATORY_PROPS: Dict[Type[TraceEvent], Dict[str, Any]] = {
    trace.TraceEvent: {},
    trace.TraceEventDurationBegin: {'ph': 'B'},
    trace.TraceEventDurationEnd: {'ph': 'E'},
    trace.TraceEventCounter: {'ph': 'C'},
    trace.TraceEventInstant: {'ph': 'i', 's': 'g'},
}


def _to_tef_event_dict(trace_event: TraceEvent) -> Dict[str, Any]:
    """Export the attributes of a TraceEvent instance to a dict.
    All public attributes of TraceEvent are exported.
    The exported timestamp is converted to micro-seconds.

    :param trace_event: Trace event to be exported.
    :return: A dict containing the attributes of the provided trace events.
    """
    tef_event_dict = {
        k: v
        for k, v in {
            **trace_event.__dict__,
            **trace_event.__class__.__dict__,
            **_TEF_MANDATORY_PROPS[trace_event.__class__],
        }.items()
        if not k.startswith('_') and k != 'tef'
    }
    tef_event_dict['ts'] *= 1e3  # timestamp in tef is in micro-seconds
    return tef_event_dict


def to_tef(
    trace_or_event: Union[Trace, TraceEvent],
    *traces_or_events: Union[Trace, TraceEvent],
    display_time_unit: str = 'ms'
) -> Dict[str, Any]:
    """Export the trace to a dict corresponding to the
    `Trace Event Format <https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview>`_
    JSON.

    If more than one traces are provided, the trace events in different traces will be merged and exported as one JSON.
    If traces and individual trace events are provided, the trace events will be merged into the exported trace.

    :param trace_or_event: A complete trace or an individual trace event to be exported.
    :param traces_or_events: More traces or trace events.
    :param display_time_unit: Specifies in which unit timestamps should be displayed.
           This supports values of "ms" or "ns". Default value is "ms".
    :return: A JSON dict in Trace Event Format.
    """
    if (
        isinstance(trace_or_event, TraceEvent) and len(traces_or_events) == 0
    ):  # Export one TraceEvent
        return _to_tef_event_dict(trace_or_event)

    # Prepare the JSON dict
    tef_trace_events: List[Dict] = []
    tef_dict = {'traceEvents': tef_trace_events}
    if display_time_unit:
        tef_dict['displayTimeUnit']: display_time_unit

    # Collect the tef dicts of provided events
    for t_or_e in (trace_or_event, *traces_or_events):
        if isinstance(t_or_e, Trace):
            tef_trace_events.extend(e.tef for e in t_or_e.events)
        elif isinstance(t_or_e, TraceEvent):
            tef_trace_events.append(_to_tef_event_dict(t_or_e))
        else:
            raise NotImplementedError

    return tef_dict
