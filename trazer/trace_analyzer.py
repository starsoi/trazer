from collections import defaultdict, deque
from enum import Enum
import math
import re
from typing import Dict, Type, Tuple, Optional
from trazer.tef import *


CODE_BASE = 52
ASCII_OFFSET = 65


class EventTypeCode(Enum):
    BEGIN = '+'
    END = '-'
    WILDCARD = '*'


class TraceAnalyzer(object):
    event_type_codes: Dict[Type, str] = {
        TraceEventDurationBegin: EventTypeCode.BEGIN.value,
        TraceEventDurationEnd: EventTypeCode.END.value,
    }
    event_type_default_code = '!'

    _re_event = re.compile(r'(\w+)(\W)')

    def __init__(self, tracer: Tracer):
        self.tracer = tracer
        self._n_codes_per_event_name = 0
        self.event_name_codes: Dict[str, str] = self._create_event_name_codes()
        self.events_string: str = self._create_events_string()

    def _validate_event_name(self, event_names: List[str]) -> None:
        """Validates all the event names and raises ValueError if any invalid event name is found in the trazer.
        Trace Analyzer has some limitation to the allowed characters in the event name, i.e. all symbols used for the
        `event_type_codes` are not allowed to appear in the event name.

        :param event_names: A list of event names.
        :return: None
        """
        invalid_characters = {*self.event_type_codes.values(),
                              self.event_type_default_code,
                              EventTypeCode.WILDCARD.value}
        for event_name in event_names:
            if not invalid_characters.isdisjoint(event_name):
                raise ValueError(
                    f'Invalid event name: "{event_name}". Characters ({", ".join(invalid_characters)}) are not allowed.'
                )

    def _create_event_name_codes(self) -> Dict[str, str]:
        """Encode event names into short alphabetic letters.
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

        self._n_codes_per_event_name = math.ceil(math.log(n_event_names, CODE_BASE)) if n_event_names > 1 else 1
        codes = [''] * n_event_names

        # Calculate the code (alphabetic letter) for each event name
        for i in range(n_event_names):
            code = ''
            q = i
            for j in range(self._n_codes_per_event_name):
                q, r = q // CODE_BASE, q % CODE_BASE
                ascii_code = ASCII_OFFSET + r
                if ascii_code > ord('Z'):  # Skip the ASCII between Z and a
                    ascii_code += 6
                code = chr(ascii_code) + code
            codes[i] = code

        return dict(zip(event_names, codes))

    def _create_wildcard_patterns(self, encoded_subpatterns: List[List[Tuple[str, str]]],
                                  exclusive_wildcard: bool = True) -> List[str]:
        """Return the pattern to replace the wildcard in the user event pattern.
        The pattern equivalent to the wildcard '*' is a non-capturing group in the form:
        (?:A[\+\-]|B[\+\-]|C[\+\-])
        where the event name codes include all possible codes.
        Depending on the event pattern, not all event types are included by the wildcard.
        The detailed exclusion rules are described in :func:_encode_event_pattern.

        :param encoded_subpatterns: List of encoded subpatterns. Each element in the ``encoded_subpatterns`` represents
               a list of explicitly specified events.
        :param exclusive_wildcard: whether explicitly specified events should be excluded from the wildcard
        :return: Regex pattern as the wildcard
        """
        wildcard_regex = f'[a-zA-Z]{{{self._n_codes_per_event_name}}}\\W'
        if not exclusive_wildcard:
            return [f'(?:{wildcard_regex})*?'] * (len(encoded_subpatterns) - 1)

        # Handle exclusive wildcards
        wildcard_patterns = []
        for i, encoded_subpattern in enumerate(encoded_subpatterns):
            if i == len(encoded_subpatterns) - 1:
                break

            excluded_end_events = []
            excluded_begin_events = []
            events_before_wildcard = defaultdict(int)
            events_after_wildcard = defaultdict(int)

            # Collect begin events specified before the wildcard.
            # These events do not end before the wildcard.
            for event_name_code, event_type_code in encoded_subpattern:
                if event_type_code == EventTypeCode.BEGIN.value:
                    events_before_wildcard[event_name_code] += 1
                elif event_type_code == EventTypeCode.END.value:
                    if events_before_wildcard[event_name_code] > 0:
                        events_before_wildcard[event_name_code] -= 1
            excluded_begin_events.extend(code for code, x in events_before_wildcard.items() if x > 0)

            # Collect end events specified after the wildcard.
            # These events do not begin after the wildcard.
            for event_name_code, event_type_code in encoded_subpatterns[i + 1]:
                if event_type_code == EventTypeCode.BEGIN.value:
                    events_after_wildcard[event_name_code] += 1
                elif event_type_code == EventTypeCode.END.value:
                    if events_after_wildcard[event_name_code] == 0:
                        events_after_wildcard[event_name_code] += 1
                    else:
                        events_after_wildcard[event_name_code] -= 1
            excluded_end_events.extend(code for code, x in events_after_wildcard.items() if x > 0)

            # Create the wildcard pattern considering the excluded events
            excluded_events = [event_name_code + '\\' + EventTypeCode.BEGIN.value
                               for event_name_code in excluded_begin_events]
            excluded_events += [event_name_code + '\\' + EventTypeCode.END.value
                                for event_name_code in excluded_end_events]
            # First event after the wildcard should not be included in the wildcard pattern,
            # because it will leads to a negative lookahead match from the wildcard pattern.
            # first_event_after_wildcard = '\\'.join(encoded_subpatterns[i + 1][0])
            # excluded_events = list(filter(lambda e: e != first_event_after_wildcard, excluded_events))
            wildcard_patterns.append(
                '(?:' +
                (f'(?!{"|".join(excluded_events)})' if len(excluded_events) else '') +
                wildcard_regex +
                ')*?'
            )

        return wildcard_patterns

    def _create_events_string(self) -> str:
        """Represent the event sequence using a string, using the following rules.
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

    def _encode_event_pattern(self, event_pattern: str, exclusive_wildcard: bool = True) -> str:
        """Replace the event name in the ``event_pattern`` with their respective alphabetic code.
        By default (``exclusive_wildcard`` = True), the wildcard excludes those events explicitly specified
        in ``event_pattern``.

        Wildcard exclusion rules are as follows.
        Consider the event pattern ``<events-before-wildcard>*<events-after-wildcard>``.

        * If an event in the ``<events-before-wildcard>`` begins but not yet ends, e.g. A+ and B+ in the pattern
        A+B+*, the wildcard will exclude the same begin events, i.e. A+ and B+. In other words, for event A and B,
        only A- and B- will be covered by the wildcard.

        * If an event in the ``<events-after-wildcard>`` ends, e.g. C- in the pattern A+B+*C-, the wildcard will
        exclude the same end events, i.e. C-. In other words, for event C, only C+ will be covered by the wildcard.

        :param event_pattern: a string for matching an event sequence
        :param exclusive_wildcard: whether explicitly specified events should be excluded from the wildcard
        :return: the encoded event pattern
        """
        # Split the event pattern by wildcard symbol
        # E.g. 'event1+event2+*event3-*event4-' is splitted into a list of subpatterns
        # ['event1+event2+', 'event3-', 'event4-']
        subpatterns: List[str] = event_pattern.split(EventTypeCode.WILDCARD.value)

        # Get a list of match objects for each subpattern
        # E.g.
        # [
        #   [<Match object for 'event1+'>, <Match object for 'event2+'>],
        #   [<Match object for 'event3-'>],
        #   [<Match object for 'event4-']
        # ]
        matches: List[List[re.Match]] = [list(self._re_event.finditer(subpattern)) for subpattern in subpatterns]
        if any(len(m) == 0 for m in matches):  # No match is found in one of the subpattern
            raise ValueError(f'Invalid event pattern "{event_pattern}"')

        last_match = matches[-1][-1]
        # Last event specification does not end at the last character of the event pattern
        # The remaining event pattern does not correspond to any event specification.
        if last_match.end() < len(subpatterns[-1]):
            raise ValueError(
                f'Invalid event pattern "{event_pattern[last_match.end():]}" at the end of "{event_pattern}".'
            )

        # Encode the subpatterns using event name codes. Each match object is converted into a tuple of
        # (event name code, event type code)
        # E.g.
        # [
        #   [('A', '+'), ('B', '+')],
        #   [('C', '-')],
        #   [('D', '-')]
        # ]
        encoded_subpatterns: List[List[Tuple[str, str]]] = []
        for i, m_one_subpattern in enumerate(matches):
            encoded_subpatterns.append([])
            for m in m_one_subpattern:
                event_name, event_type_code = m.group(1), m.group(2)
                if event_name not in self.event_name_codes:
                    raise ValueError(f'Event name "{event_name}" not found in the trazer.')
                if event_type_code not in [*self.event_type_codes.values(), self.event_type_default_code]:
                    raise ValueError(f'Invalid character "{event_type_code}" in the event pattern "{event_pattern}".')

                event_name_code = self.event_name_codes[event_name]
                encoded_subpatterns[i].append((event_name_code, event_type_code))

        wildcard_patterns = self._create_wildcard_patterns(encoded_subpatterns, exclusive_wildcard)

        encoded_event_pattern = ''
        for i, encoded_subpattern in enumerate(encoded_subpatterns):
            encoded_event_pattern += ''.join(f'({event_name_code})\\{event_type_code}'
                                             for event_name_code, event_type_code in encoded_subpattern)
            if i < len(encoded_subpatterns) - 1:
                encoded_event_pattern += wildcard_patterns[i]

        return encoded_event_pattern

    def _map_string_index_to_event(self, event_string_index: int):
        """Map the index of the ``events_string`` to the represented trazer event object.
        The length of a single event in the ``events_string`` is always ``_n_codes_per_event_name + 1``.
        Therefore, ``event_string_index // (_n_codes_per_event_name + 1)`` is the index of the corresponding
        trazer event object in the ``tracer``.
        :param event_string_index: The index of an event name code in the ``events_string``.
        :return: The corresponding trazer event object.
        """
        return self.tracer.events[event_string_index // (self._n_codes_per_event_name + 1)]

    def merge_events(self, event_pattern: str, merged_event_name: str, pid: int = 1000) -> None:
        """Create a new event for a specific event sequence matching the given ``event_pattern``.
        The new event is typically assigned to a different pid than the original events, so that they can be visualized
        in a different group.

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

        The resulted merged event sequence will be:
        [0.001 s]: Begin request_event
        [0.003 s]: End   request_event
        [0.004 s]: Begin response_event
        [0.008 s]: End   response_event

        :param event_pattern: a string for matching an event sequence
        :param merged_event_name: the name of the new event for the matched event sequence
        :param pid: pid for the merged event
        :return: None
        """
        encoded_event_pattern = self._encode_event_pattern(event_pattern)
        for m in re.finditer(encoded_event_pattern, self.events_string):
            first_event = self._map_string_index_to_event(m.start(1))
            last_event = self._map_string_index_to_event(m.start(len(m.groups())))

            self.tracer.add_event(TraceEventDurationBegin(merged_event_name, first_event._ts, pid))
            self.tracer.add_event(TraceEventDurationEnd(merged_event_name, last_event._ts, pid))
