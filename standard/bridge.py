import threading
from contextlib import contextmanager

from koskript import Errors

from .helpers import type_name

_runtime = None
_lock = threading.RLock()


def use(runtime):
    global _runtime
    _runtime = runtime
    return runtime


def lock():
    return _lock


@contextmanager
def guarded():
    with _lock:
        yield


def execute(code):
    if _runtime is None:
        raise Errors.RuntimeError("no runtime is registered for background tasks")

    with _lock:
        return _runtime.execute(code)


def call(function, *values):
    if function is None:
        return None

    with _lock:
        if _runtime is not None:
            interpreter = getattr(_runtime, "__interpreter__", None)

            if interpreter is None:
                interpreter = getattr(_runtime, "_KoskriptRuntime__interpreter__", None)

            if interpreter is not None and hasattr(interpreter, "call_value"):
                return interpreter.call_value(function, list(values))

        if callable(function):
            return function(*values)

    raise Errors.MismatchType(f"{type_name(function)} is not callable")
