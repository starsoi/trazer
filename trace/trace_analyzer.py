import math
import re
from typing import Dict, Type
from trace.tef import *


CODE_BASE = 52
ASCII_OFFSET = 65


class TraceAnalyzer(object):
    event_type_codes: Dict[Type, str] = {
        TraceEventDurationBegin: '+',
        TraceEventDurationEnd: '-',
    }
    event_type_default_code: str = '!'

    def __init__(self, tracer: Tracer):
        self.tracer = tracer
        self.event_name_codes: Dict[str, str] = self._create_event_name_codes()
        self.events_string: str = self._create_events_string()

    def _validate_event_name(self, event_names) -> None:
        """
        Trace Analyzer has some limitation to the allowed characters in the event name, i.e. all symbols used for the
        `event_type_codes` are not allowed to appear in the event name.
        This function validates all the event names and raises ValueError if any invalid event name is found in the
        trace.
        :return: None
        """
        invalid_characters = set(self.event_type_codes.values())
        invalid_characters.add(self.event_type_default_code)
        for event_name in event_names:
            if not invalid_characters.isdisjoint(event_name):
                raise ValueError(
                    f'Invalid event name: "{event_name}". Characters ({", ".join(invalid_characters)}) are not allowed.'
                )

    def _create_event_name_codes(self) -> Dict[str, str]:
        """
        Encode event names into short alphabetic letters.
        The case-sensitive letters A-Z and a-z are used, which are used to represent 1st-26th and 27th-52th event names.
        For example,
            'event1' -> 'A',
            'event2' -> 'B',
            ...,
            'event26' -> 'Z',
            'event27' -> 'a',
            'event28' -> 'b',
            ...

        If the number of event names is greater than 52, two letters are used, i.e. AA-ZZ and aa-zz. Basically, it is a
        base-52 number system using alphabetic letters to encode the event names into shorter strings.

        :return: a dictionary for the mapping from event name to the corresponding alphabetic codes
        """
        # Collect all event names
        event_names = sorted(set(e.name for e in self.tracer.events))
        n_event_names = len(event_names)
        if n_event_names == 0:
            return {}
        self._validate_event_name(event_names)

        n_codes_per_event_name = math.ceil(math.log(n_event_names, CODE_BASE)) if n_event_names > 1 else 1
        codes = [''] * n_event_names

        # Calculate the code (alphabetic letter) for each event name
        for i in range(n_event_names):
            code = ''
            q = i
            for j in range(n_codes_per_event_name):
                q, r = q // CODE_BASE, q % CODE_BASE
                ascii_code = ASCII_OFFSET + r
                if ascii_code > ord('Z'):  # Skip the ASCII between Z and a
                    ascii_code += 6
                code = chr(ascii_code) + code
            codes[i] = code

        return dict(zip(event_names, codes))

    def _create_events_string(self) -> str:
        """
        Represent the event sequence using a string, using the following rules.
          * The event names are represented using the alphabetic codes.
          * The duration begin event has a suffix '+'
          * The duration end event has a suffix '-'
          * Other event types has a suffix '!'

        For example, if we have a event sequence is ['duration_event1_begin', 'duration_event1_end', 'instant_event'].
        The event name codes mappings will be 'duration_event1': 'A' and 'instant_event': 'B'.

        The events string will then be 'A+A-B!'

        :return: the encoded string for the event sequence
        """
        events_string = ''
        for event in self.tracer.events:
            event_name_code = self.event_name_codes[event.name]
            event_type_code = self.event_type_codes.get(event.__class__, self.event_type_default_code)
            events_string += event_name_code + event_type_code
        return events_string

    def merge_events(self, event_pattern: str, merged_event_name: str, pid=1000) -> None:
        """
        Create a new event for a specific event sequence matching the given `event_pattern`.
        The new event is typically assigned to a different pid than the original events.

        For example, we have an event sequence for processing a network message:
        [0.001 s]: Begin receive_request_msg
        [0.002 s]: Begin process_request_msg
        [0.003 s]: End   process_request_msg
        [0.004 s]: Begin prepare_response_msg
        [0.005 s]: End   prepare_response_msg
        [0.006 s]: Begin send_response_msg
        [0.007 s]: End   send_response_msg
        [0.008 s]: End   receive_request_msg
        The events are stored in the `network_tracer` object.

        If we focus on the duration of request and response, respectively, we can merge the request-related events
        into an request-event and response-related events into an response-event by calling
        >>> trace_analyzer = TraceAnalyzer(network_tracer)
        >>> trace_analyzer.merge_events('receive_request_msg+*process_request_msg-', 'request_event')
        >>> trace_analyzer.merge_events('prepare_response_msg+*receive_request_msg-', 'response_event')

        Usage of symbols in `event_pattern`:
        '+' following an event name: the event begins
        '-' following an event name: the event ends
        '*': arbitrary events

        :param event_pattern: a string for matching an event sequence
        :param merged_event_name: the name of the new event for the matched event sequence
        :param pid: pid for the merged event
        :return: None
        """
        raise NotImplementedError()
