import inspect
import platform

import requests
from koskript import Errors

from .helpers import expect_int, expect_number, expect_string, guard
from .output import Output


def _members(target):
    members = []

    for name, value in inspect.getmembers(target):
        if name.startswith("_") or not callable(value):
            continue

        try:
            signature = str(inspect.signature(value))
        except (TypeError, ValueError):
            signature = "(...)"

        members.append((name, signature))

    return sorted(members)


class Koshell:
    def __init__(self, runtime, modules=None, version="2.0.0"):
        self._runtime = runtime
        self._modules = modules or {}
        self.version = version

    def execute(self, code):
        expect_string("koshell.execute", code)
        return self._runtime.execute(code)

    def eval(self, code):
        return self.execute(code)

    def source(self, path):
        expect_string("koshell.source", path)

        with guard("koshell.source", UnicodeDecodeError):
            with open(path, "r", encoding="utf-8") as file:
                code = file.read()

        return self._runtime.execute(code)

    def loadfrom(self, url, timeout=10):
        expect_string("koshell.loadfrom", url)
        expect_number("koshell.loadfrom", timeout)

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException:
            return False

        return self._runtime.execute(response.text)

    def modules(self):
        return sorted(self._modules.keys())

    def help(self, name=None):
        if name is None:
            lines = [f"Koshell {self.version} standard modules:"]

            for module in self.modules():
                lines.append(f"  {module} ({len(_members(self._modules[module]))} functions)")

            lines.append("Use koshell.help(\"module\") to list its functions.")
            return "\n".join(lines)

        expect_string("koshell.help", name)

        if name not in self._modules:
            raise Errors.RuntimeError(f"koshell.help() unknown module '{name}'")

        lines = [f"{name}:"]

        for member, signature in _members(self._modules[name]):
            lines.append(f"  {name}.{member}{signature}")

        return "\n".join(lines)

    def about(self):
        return {
            "name": "Koshell",
            "version": self.version,
            "python": platform.python_version(),
            "modules": self.modules(),
            "module_count": len(self._modules),
        }

    def clear(self):
        Output.clear()

    def exit(self, code=0):
        expect_int("koshell.exit", code)
        raise SystemExit(code)
