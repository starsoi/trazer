# Trazer

![Test](https://github.com/starsoi/trazer/actions/workflows/main.yml/badge.svg)
![Doctest](https://github.com/starsoi/trazer/actions/workflows/doctest.yml/badge.svg)
[![Coverage](https://codecov.io/gh/starsoi/trazer/branch/master/graph/badge.svg?token=HVX3PFO8RF)](https://codecov.io/gh/starsoi/trazer)

A general trace analysis framework for program and network traces.


## Getting Started

### Prerequisites

* Python >= 3.7

## Usage

### Create Trace and Add Events
```python
>>> from trazer.trace import Trace, TraceEventDurationBegin, TraceEventDurationEnd
>>> trace = Trace()
>>> trace.add_event(TraceEventDurationBegin('my_event', 1.0))  # my_event begins at 1.0 ms
>>> trace.add_event(TraceEventDurationEnd('my_event', 2.0))  # my_event ends at 1.0 ms

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

## Contributing

1. Install development dependencies
```bash
pip3 install -r requirements-dev.txt
```

2. Install runtime dependencies
```bash
pip3 install -r requirements.txt
```

3. Setup pre-commit hook (formatting with black)
```bash
pre-commit install
```

4. Make sure to run `pytest` for testing
