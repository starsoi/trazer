from trace.tef import Tracer, TraceEventDurationBegin


def create_test_trace():
    tracer = Tracer()
    e = TraceEventDurationBegin('test_event', 123)
    print(e.tef)


if __name__ == '__main__':
    create_test_trace()
