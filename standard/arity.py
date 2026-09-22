import functools
import inspect

from koskript import Errors


def _checked(name, function):
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return function

    parameters = list(signature.parameters.values())
    positional = [
        parameter for parameter in parameters
        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    variadic = any(parameter.kind == parameter.VAR_POSITIONAL for parameter in parameters)
    minimum = sum(1 for parameter in positional if parameter.default is parameter.empty)
    maximum = len(positional)

    @functools.wraps(function)
    def wrapper(*args):
        count = len(args)

        if count < minimum or (not variadic and count > maximum):
            if variadic:
                expected = f"at least {minimum}"
            elif minimum == maximum:
                expected = f"{minimum}"
            else:
                expected = f"between {minimum} and {maximum}"

            raise Errors.MismatchType(
                f"{name}() expected {expected} argument(s), got {count}")

        return function(*args)

    return wrapper


def wrap(module_name, target):
    if not inspect.isclass(target):
        return _checked(module_name, target)

    namespace = {}

    for name, value in vars(target).items():
        if name.startswith("_") or not callable(value):
            continue
        namespace[name] = _checked(f"{module_name}.{name}", value)

    return type(target.__name__, (target,), namespace)
