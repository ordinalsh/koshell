import threading
import time

from koskript import Errors

from . import bridge
from .helpers import expect_int, expect_number, expect_string, type_name
from .output import Output

_JOBS = {}
_NEXT_ID = 1
_LOCK = threading.RLock()
_STOP = threading.Event()
_THREAD = None


class _Job:
    def __init__(self, job_id, name, kind, interval, callback):
        self.id = job_id
        self.name = name
        self.kind = kind
        self.interval = interval
        self.callback = callback
        self.enabled = True
        self.runs = 0
        self.last_run = None
        self.next_run = time.time() + interval


def _validate_callback(label, callback):
    if callback is None:
        raise Errors.MismatchType(f"{label}() expected a callback, got null")

    if isinstance(callback, str) or callable(callback):
        return callback

    if type(callback).__name__ in ("Function", "BoundMethod"):
        return callback

    raise Errors.MismatchType(f"{label}() expected a callback, got {type_name(callback)}")


def _execute(job):
    try:
        if isinstance(job.callback, str):
            bridge.execute(job.callback)
        else:
            bridge.call(job.callback)
    except SystemExit:
        with _LOCK:
            _JOBS.pop(job.id, None)
    except Exception as error:
        Output.error(f"tasks.{job.name}() failed: {type(error).__name__}: {error}")


def _fire(job):
    with _LOCK:
        if job.kind == "once":
            _JOBS.pop(job.id, None)

        job.runs += 1
        job.last_run = time.time()

        if job.kind == "every":
            job.next_run = job.last_run + job.interval

    _execute(job)


def _loop():
    while not _STOP.is_set():
        now = time.time()

        with _LOCK:
            due = [job for job in _JOBS.values() if job.enabled and job.next_run <= now]

        for job in due:
            _fire(job)

        _STOP.wait(0.2)


def _ensure_thread():
    global _THREAD

    if _THREAD is not None and _THREAD.is_alive():
        return

    _STOP.clear()
    _THREAD = threading.Thread(target=_loop, name="koshell-tasks", daemon=True)
    _THREAD.start()


def _schedule(kind, seconds, callback, name, label):
    expect_number(label, seconds)
    callback = _validate_callback(label, callback)

    if seconds <= 0:
        raise Errors.RuntimeError(f"{label}() expected a positive interval")

    if name is not None:
        expect_string(label, name)

    global _NEXT_ID

    with _LOCK:
        job_id = _NEXT_ID
        _NEXT_ID += 1
        _JOBS[job_id] = _Job(job_id, name or f"task-{job_id}", kind, seconds, callback)

    _ensure_thread()
    return job_id


class Tasks:
    def every(seconds, callback, name=None):
        return _schedule("every", seconds, callback, name, "tasks.every")

    def every_minutes(minutes, callback, name=None):
        expect_number("tasks.every_minutes", minutes)
        return _schedule("every", minutes * 60, callback, name, "tasks.every_minutes")

    def every_hours(hours, callback, name=None):
        expect_number("tasks.every_hours", hours)
        return _schedule("every", hours * 3600, callback, name, "tasks.every_hours")

    def after(seconds, callback, name=None):
        return _schedule("once", seconds, callback, name, "tasks.after")

    def list():
        now = time.time()

        with _LOCK:
            jobs = sorted(_JOBS.values(), key=lambda job: job.id)

            return [
                {
                    "id": job.id,
                    "name": job.name,
                    "kind": job.kind,
                    "interval": job.interval,
                    "remaining": max(0.0, round(job.next_run - now, 3)),
                    "last": job.last_run,
                    "runs": job.runs,
                    "enabled": job.enabled,
                }
                for job in jobs
            ]

    def cancel(job_id):
        expect_int("tasks.cancel", job_id)

        with _LOCK:
            return _JOBS.pop(job_id, None) is not None

    def pause(job_id):
        expect_int("tasks.pause", job_id)

        with _LOCK:
            job = _JOBS.get(job_id)

            if job is None:
                return False

            job.enabled = False
            return True

    def resume(job_id):
        expect_int("tasks.resume", job_id)

        with _LOCK:
            job = _JOBS.get(job_id)

            if job is None:
                return False

            job.enabled = True
            job.next_run = time.time() + job.interval
            return True

    def trigger(job_id):
        expect_int("tasks.trigger", job_id)

        with _LOCK:
            job = _JOBS.get(job_id)

        if job is None:
            return False

        _fire(job)
        return True

    def clear():
        with _LOCK:
            count = len(_JOBS)
            _JOBS.clear()

        return count
