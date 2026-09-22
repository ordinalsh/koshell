import getpass
import locale as locale_module
import os
import platform as platform_module
import shutil
import subprocess
import sys
import time

import psutil
from koskript import Errors

from .helpers import expect_number, expect_string, guard, human_size


class System:
    def platform():
        return platform_module.system()

    def release():
        return platform_module.release()

    def version():
        return platform_module.version()

    def machine():
        return platform_module.machine()

    def hostname():
        return platform_module.node()

    def user():
        return getpass.getuser()

    def home():
        return os.path.expanduser("~")

    def python():
        return platform_module.python_version()

    def cpu_count(logical=True):
        if logical:
            return psutil.cpu_count(logical=True) or 1
        return psutil.cpu_count(logical=False) or 1

    def cpu_percent(interval=0.0):
        expect_number("system.cpu_percent", interval)
        return psutil.cpu_percent(interval=interval)

    def memory():
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
            "total_human": human_size(memory.total),
            "used_human": human_size(memory.used),
            "available_human": human_size(memory.available),
        }

    def swap():
        swap = psutil.swap_memory()
        return {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent": swap.percent,
            "total_human": human_size(swap.total),
            "used_human": human_size(swap.used),
        }

    def disk(path="."):
        expect_string("system.disk", path)
        with guard("system.disk"):
            usage = shutil.disk_usage(path)
        return {
            "path": os.path.abspath(path),
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": round(usage.used / usage.total * 100, 2),
            "total_human": human_size(usage.total),
            "used_human": human_size(usage.used),
            "free_human": human_size(usage.free),
        }

    def boot_time():
        return psutil.boot_time()

    def uptime():
        return time.time() - psutil.boot_time()

    def locale():
        try:
            return locale_module.getlocale()[0] or "unknown"
        except ValueError:
            return "unknown"

    def timezone():
        return time.tzname[0] if time.tzname else "unknown"

    def open(path):
        expect_string("system.open", path)

        if not os.path.exists(path):
            raise Errors.RuntimeError(f"system.open() path does not exist: {path}")

        try:
            if hasattr(os, "startfile"):
                os.startfile(path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.Popen([opener, path])
        except OSError as error:
            raise Errors.RuntimeError(f"system.open() failed: {error}") from None

        return True

    def info():
        return {
            "platform": System.platform(),
            "release": System.release(),
            "version": System.version(),
            "machine": System.machine(),
            "hostname": System.hostname(),
            "user": System.user(),
            "home": System.home(),
            "python": System.python(),
            "cpu_count": System.cpu_count(),
            "cpu_percent": System.cpu_percent(),
            "memory": System.memory(),
            "disk": System.disk(),
            "uptime": System.uptime(),
            "timezone": System.timezone(),
        }
