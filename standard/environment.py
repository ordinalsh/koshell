import os

from .helpers import expect_string


class Environment:
    def get(name, default=None):
        expect_string("env.get", name)
        return os.environ.get(name, default)

    def set(name, value):
        expect_string("env.set", name)
        expect_string("env.set", value)
        os.environ[name] = value
        return value

    def unset(name):
        expect_string("env.unset", name)
        return os.environ.pop(name, None) is not None

    def has(name):
        expect_string("env.has", name)
        return name in os.environ

    def all():
        return dict(os.environ)

    def expand(text):
        expect_string("env.expand", text)
        return os.path.expandvars(text)

    def path():
        return [part for part in os.environ.get("PATH", "").split(os.pathsep) if part]

    def add_path(directory):
        expect_string("env.add_path", directory)
        parts = Environment.path()

        if directory not in parts:
            parts.append(directory)

        os.environ["PATH"] = os.pathsep.join(parts)
        return directory

    def remove_path(directory):
        expect_string("env.remove_path", directory)
        parts = [part for part in Environment.path() if part != directory]
        os.environ["PATH"] = os.pathsep.join(parts)
        return directory
