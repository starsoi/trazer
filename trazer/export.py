from typing import Any, Dict, IO, List, Optional, Type, Union
from trazer import Trace
import trazer.trace as trace
from trazer.trace import TraceEvent


_TEF_MANDATORY_PROPS: Dict[Type[TraceEvent], Dict[str, Any]] = {
    trace.TraceEvent: {},
    trace.TraceEventDurationBegin: {'ph': 'B'},
    trace.TraceEventDurationEnd: {'ph': 'E'},
    trace.TraceEventCounter: {'ph': 'C'},
    trace.TraceEventInstant: {'ph': 'i', 's': 'g'},
    trace.TraceEventMetadata: {'ph': 'M'},
    trace.TraceEventFlowStart: {'ph': 's'},
    trace.TraceEventFlowEnd: {'ph': 'f'},
}


def to_tef_event_dict(trace_event: TraceEvent, time_unit: str = 'ms') -> Dict[str, Any]:
    """Export the attributes of a TraceEvent instance to a dict.
    All public attributes of TraceEvent are exported.
    The exported timestamp is converted to the unit specified by ``time_unit``.

    :param trace_event: Trace event to be exported.
    :param time_unit: Time unit of the exported timestamps.
           The unit of timestamp for a ``TraceEvent`` is in second.
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
    if 'ts' in tef_event_dict:
        if time_unit == 'ms':
            tef_event_dict['ts'] *= 1e3
        elif time_unit == 'us':
            tef_event_dict['ts'] *= 1e6
        elif time_unit == 'ns':
            tef_event_dict['ts'] *= 1e9
    return tef_event_dict


def to_tef_json(
    trace_or_event: Union[Trace, TraceEvent],
    *traces_or_events: Union[Trace, TraceEvent],
    display_time_unit: str = 'ms',
    file_like: Optional[IO[str]] = None
) -> Optional[Dict[str, Any]]:
    """Export the trace to a JSON corresponding to the
    `Trace Event Format <https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview>`_

    If more than one traces are provided, the trace events in different traces will be merged and exported as one JSON.
    If traces and individual trace events are provided, the trace events will be merged into the exported trace.

    :param trace_or_event: A complete trace or an individual trace event to be exported.
    :param traces_or_events: More traces or trace events.
    :param display_time_unit: Specifies in which unit timestamps should be displayed.
           This supports values of "ms" or "ns". Default value is "ms".
    :param file_like: A file-like object for writing the JSON.
    :return: The JSON dict in Trace Event Format or None if ``file_path`` is provided.
    """
    import json

    # Prepare the JSON dict
    tef_trace_events: List[Dict] = []
    tef_dict = {'traceEvents': tef_trace_events, 'displayTimeUnit': display_time_unit}

    # Collect the tef dicts of provided events
    for t_or_e in (trace_or_event, *traces_or_events):
        if isinstance(t_or_e, Trace):
            tef_trace_events.extend(
                to_tef_event_dict(e, display_time_unit)
                for e in t_or_e.events + t_or_e.metadata_events
            )
        elif isinstance(t_or_e, TraceEvent):
            tef_trace_events.append(to_tef_event_dict(t_or_e, display_time_unit))
        else:
            raise NotImplementedError

    if file_like:
        json.dump(tef_dict, file_like, indent=4)
    else:
        return tef_dict
