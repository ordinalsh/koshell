import inspect
from contextlib import contextmanager

from koskript import Errors


def type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (list, tuple)):
        return "array"
    if isinstance(value, dict):
        return "map"
    if inspect.isclass(value):
        return "class"
    return type(value).__name__


def arity(name, args, minimum, maximum=None):
    count = len(args)
    if count >= minimum and (maximum is None or count <= maximum):
        return

    if maximum is None:
        expected = f"at least {minimum}"
    elif minimum == maximum:
        expected = f"{minimum}"
    else:
        expected = f"between {minimum} and {maximum}"

    raise Errors.MismatchType(f"{name}() expected {expected} argument(s), got {count}")


def expect_string(name, value):
    if not isinstance(value, str):
        raise Errors.MismatchType(f"{name}() expected a string, got {type_name(value)}")
    return value


def expect_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise Errors.MismatchType(f"{name}() expected an int, got {type_name(value)}")
    return value


def expect_number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Errors.MismatchType(f"{name}() expected a number, got {type_name(value)}")
    return value


def expect_array(name, value):
    if not isinstance(value, (list, tuple)):
        raise Errors.MismatchType(f"{name}() expected an array, got {type_name(value)}")
    return value


def expect_map(name, value):
    if not isinstance(value, dict):
        raise Errors.MismatchType(f"{name}() expected a map, got {type_name(value)}")
    return value


def expect_bool(name, value):
    if not isinstance(value, bool):
        raise Errors.MismatchType(f"{name}() expected a bool, got {type_name(value)}")
    return value


def human_size(size):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(size)
    index = 0

    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1

    if index == 0:
        return f"{int(value)} {units[index]}"

    return f"{value:.2f} {units[index]}"


@contextmanager
def guard(name, *exceptions):
    try:
        yield
    except (Errors.SyntaxError, Errors.NameError, Errors.MismatchType,
            Errors.ProtectedObject, Errors.RuntimeError):
        raise
    except OSError as error:
        detail = error.strerror or error

        if getattr(error, "filename", None):
            detail = f"{detail}: {error.filename}"

        raise Errors.RuntimeError(f"{name}() failed: {detail}") from None
    except exceptions as error:
        raise Errors.RuntimeError(f"{name}() failed: {error}") from None
