import os
import shutil
import subprocess
import time

import psutil

from koskript import Errors

from .helpers import expect_array, expect_int, expect_number, expect_string, guard, human_size

_PSUTIL_ERRORS = (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess)


def _task(process):
    with process.oneshot():
        memory = process.memory_info().rss
        info = {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),
            "memory": memory,
            "memory_human": human_size(memory),
            "threads": process.num_threads(),
            "created": process.create_time(),
            "user": None,
        }

    try:
        info["user"] = process.username()
    except _PSUTIL_ERRORS:
        info["user"] = None

    return info


class Process:
    def get_tasks():
        tasks = []
        for process in psutil.process_iter():
            try:
                tasks.append(_task(process))
            except _PSUTIL_ERRORS:
                continue
        return tasks

    def find(name):
        expect_string("process.find", name)
        needle = name.lower()
        return [task for task in Process.get_tasks() if needle in task["name"].lower()]

    def info(pid):
        expect_int("process.info", pid)
        try:
            return _task(psutil.Process(pid))
        except _PSUTIL_ERRORS:
            return None

    def exists(pid):
        expect_int("process.exists", pid)
        return psutil.pid_exists(pid)

    def pid():
        return os.getpid()

    def parent(pid):
        expect_int("process.parent", pid)
        try:
            parent = psutil.Process(pid).parent()
        except _PSUTIL_ERRORS:
            return None
        return None if parent is None else _task(parent)

    def children(pid):
        expect_int("process.children", pid)
        try:
            return [_task(child) for child in psutil.Process(pid).children()]
        except _PSUTIL_ERRORS:
            return []

    def cmdline(pid):
        expect_int("process.cmdline", pid)
        try:
            return psutil.Process(pid).cmdline()
        except _PSUTIL_ERRORS:
            return []

    def cwd(pid):
        expect_int("process.cwd", pid)
        try:
            return psutil.Process(pid).cwd()
        except _PSUTIL_ERRORS:
            return None

    def wait(pid, timeout=None):
        expect_int("process.wait", pid)
        if timeout is not None:
            expect_number("process.wait", timeout)

        try:
            psutil.Process(pid).wait(timeout=timeout)
            return True
        except psutil.TimeoutExpired:
            return False
        except _PSUTIL_ERRORS:
            return False

    def terminate_task(pid):
        expect_int("process.terminate_task", pid)
        if not psutil.pid_exists(pid):
            return False

        try:
            psutil.Process(pid).terminate()
        except psutil.AccessDenied:
            raise Errors.RuntimeError(f"process.terminate_task() access denied for pid {pid}") from None
        except psutil.NoSuchProcess:
            return False

        return True

    def kill_task(pid):
        expect_int("process.kill_task", pid)
        if not psutil.pid_exists(pid):
            return False

        try:
            psutil.Process(pid).kill()
        except psutil.AccessDenied:
            raise Errors.RuntimeError(f"process.kill_task() access denied for pid {pid}") from None
        except psutil.NoSuchProcess:
            return False

        return True

    def suspend(pid):
        expect_int("process.suspend", pid)
        try:
            psutil.Process(pid).suspend()
        except _PSUTIL_ERRORS:
            return False
        return True

    def resume(pid):
        expect_int("process.resume", pid)
        try:
            psutil.Process(pid).resume()
        except _PSUTIL_ERRORS:
            return False
        return True

    def run(command, cwd=None, timeout=None, shell=True):
        if isinstance(command, str):
            target = command
        else:
            expect_array("process.run", command)
            target = [str(part) for part in command]
            shell = False

        if cwd is not None:
            expect_string("process.run", cwd)
        if timeout is not None:
            expect_number("process.run", timeout)

        start = time.time()

        try:
            result = subprocess.run(
                target, cwd=cwd, timeout=timeout, shell=shell,
                capture_output=True, text=True, errors="replace")
        except subprocess.TimeoutExpired:
            raise Errors.RuntimeError(
                f"process.run() timed out after {timeout} second(s)") from None
        except OSError as error:
            raise Errors.RuntimeError(
                f"process.run() failed: {error.strerror or error}") from None

        return {
            "code": result.returncode,
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": time.time() - start,
        }

    def spawn(command, cwd=None):
        if isinstance(command, str):
            target = command
            shell = True
        else:
            expect_array("process.spawn", command)
            target = [str(part) for part in command]
            shell = False

        if cwd is not None:
            expect_string("process.spawn", cwd)

        options = {"cwd": cwd, "shell": shell}
        if os.name == "nt":
            options["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            options["start_new_session"] = True

        with guard("process.spawn"):
            process = subprocess.Popen(target, **options)

        return process.pid

    def which(command):
        expect_string("process.which", command)
        return shutil.which(command)

    def top(limit=10, by="memory"):
        expect_int("process.top", limit)
        expect_string("process.top", by)

        if by not in ("memory", "cpu"):
            raise Errors.MismatchType("process.top() expected 'memory' or 'cpu'")

        tasks = Process.get_tasks()

        if by == "cpu":
            for task in tasks:
                try:
                    task["cpu"] = psutil.Process(task["pid"]).cpu_percent(interval=None)
                except _PSUTIL_ERRORS:
                    task["cpu"] = 0.0
            tasks.sort(key=lambda task: task.get("cpu", 0.0), reverse=True)
        else:
            tasks.sort(key=lambda task: task["memory"], reverse=True)

        return tasks[:limit]
