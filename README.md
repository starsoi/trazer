# Trazer

![Test](https://github.com/starsoi/trazer/actions/workflows/main.yml/badge.svg)
![Doctest](https://github.com/starsoi/trazer/actions/workflows/doctest.yml/badge.svg)
[![Coverage](https://codecov.io/gh/starsoi/trazer/branch/master/graph/badge.svg?token=HVX3PFO8RF)](https://codecov.io/gh/starsoi/trazer)

A general trace analysis framework (**tra**ce analy**zer**) for execution and network traces, 
focusing on event chain analysis.


## Getting Started

### Prerequisites

* Python >= 3.8

## Usage

### Create Trace and Add Events
```python
>>> from trazer.trace import Trace, TraceEventDurationBegin, TraceEventDurationEnd
>>> trace = Trace()
>>> trace.add_event(TraceEventDurationBegin('my_event', 1.0))  # my_event begins at 1.0 ms
>>> trace.add_event(TraceEventDurationEnd('my_event', 2.0))  # my_event ends at 2.0 ms

```

### Export Trace to Chrome Tracing JSON
```python
>>> print(trace.tef_json)  # Exported timestamps are in microsecond  
{
    "traceEvents": [
        {
            "name": "my_event",
            "ts": 1000.0,
            "pid": 0,
            "tid": 0,
            "args": {},
            "ph": "B"
        },
        {
            "name": "my_event",
            "ts": 2000.0,
            "pid": 0,
            "tid": 0,
            "args": {},
            "ph": "E"
        }
    ],
    "displayTimeUnit": "ms"
}

```

Next, store the string into a `.json` file and open it using the trace tool `chrome://tracing` in Chrome.

### Merge Event Chains

Different related events in an event chain can be merged and represented as a merged event in the higher hierarchical level.

An event chain is described using an event pattern. Special symbols in the notation:

* `+` following an event name: the event begins.
* `-` following an event name: the event ends.
* `*`: arbitrary events, excluding repetitions.

```python
>>> from trazer.trace import Trace, TraceEventDurationBegin, TraceEventDurationEnd
>>> trace = Trace()

# Add an event chain: event1 begins -> event2 begins -> event2 ends -> event1 ends
>>> trace.add_events([
... TraceEventDurationBegin('event1', 1),
... TraceEventDurationBegin('event2', 2),
... TraceEventDurationEnd('event2', 3),
... TraceEventDurationEnd('event1', 4)
... ])

>>> print(trace)
[1 ms]: event1 (B)
[2 ms]: event2 (B)
[3 ms]: event2 (E)
[4 ms]: event1 (E)

>>> from trazer.analyzer import TraceAnalyzer
>>> trace_analyzer = TraceAnalyzer(trace)

# Merge all events belonging to the event chain
>>> print(trace_analyzer.merge_events('event1+event2+event2-event1-', 'event_chain'))
[1 ms]: event_chain (B)
[4 ms]: event_chain (E)

# Or use an alternative pattern employing wildcards
>>> trace_analyzer = TraceAnalyzer(trace)
>>> print(trace_analyzer.merge_events('event1+*-event1-', 'event_chain'))
[1 ms]: event_chain (B)
[4 ms]: event_chain (E)

```

### Export Trace with Merged Events

The merged events can be visualized together with the original trace in the same view.
For visualization in `chrome://tracing`, a dedicated process ID needs to be assigned to
the merged events, such that they will be displayed separately from the original trace.

```python
trace_analyzer.to_tef_json(5555)  # Process ID = 5555
```

## Contributing

1. Install development dependencies
```bash
pip3 install -r requirements-dev.txt
```

2. Install runtime dependencies
```bash
pip3 install -r requirements.txt
```

3. Setup pre-commit hook (formatting with black and linting with flake8)
```bash
pre-commit install
```

4. Make sure to run `pytest` for testing
