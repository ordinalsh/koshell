import os
from datetime import datetime

from koskript import Errors

from .helpers import expect_int, expect_string, guard

LEVELS = ("debug", "info", "warn", "error")


class Logger:
    def levels():
        return list(LEVELS)

    def write(path, message, level="info"):
        expect_string("logger.write", path)
        expect_string("logger.write", level)
        expect_string("logger.write", message)

        level = level.lower()
        if level not in LEVELS:
            raise Errors.RuntimeError(f"logger.write() unknown level '{level}'")

        stamp = datetime.now().isoformat(timespec="seconds")

        with guard("logger.write"):
            with open(path, "a", encoding="utf-8") as file:
                file.write(f"[{stamp}] {level.upper()} {message}\n")

        return path

    def read(path, lines=20):
        expect_string("logger.read", path)
        expect_int("logger.read", lines)

        with guard("logger.read"):
            if not os.path.exists(path):
                return []

            with open(path, "r", encoding="utf-8") as file:
                content = file.read().splitlines()

        if lines <= 0:
            return content

        return content[-lines:]

    def tail(path, lines=20):
        return Logger.read(path, lines)

    def clear(path):
        expect_string("logger.clear", path)

        with guard("logger.clear"):
            with open(path, "w", encoding="utf-8") as file:
                file.write("")

        return path

    def size(path):
        expect_string("logger.size", path)

        with guard("logger.size"):
            return os.path.getsize(path)

    def exists(path):
        expect_string("logger.exists", path)
        return os.path.exists(path)
