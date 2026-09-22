import time
from datetime import datetime, timezone

from .helpers import expect_number, expect_string


def _stamp(name, timestamp):
    if timestamp is None:
        return time.time()
    return expect_number(name, timestamp)


class Clock:
    def now():
        return time.time()

    def utc_now():
        return datetime.now(timezone.utc).timestamp()

    def iso(timestamp=None):
        moment = datetime.fromtimestamp(_stamp("clock.iso", timestamp))
        return moment.isoformat(timespec="seconds")

    def utc_iso(timestamp=None):
        moment = datetime.fromtimestamp(_stamp("clock.utc_iso", timestamp), timezone.utc)
        return moment.isoformat(timespec="seconds")

    def date(timestamp=None):
        moment = datetime.fromtimestamp(_stamp("clock.date", timestamp))
        return moment.strftime("%Y-%m-%d")

    def time(timestamp=None):
        moment = datetime.fromtimestamp(_stamp("clock.time", timestamp))
        return moment.strftime("%H:%M:%S")

    def weekday(timestamp=None):
        moment = datetime.fromtimestamp(_stamp("clock.weekday", timestamp))
        return moment.strftime("%A")

    def format(timestamp, pattern):
        expect_string("clock.format", pattern)
        moment = datetime.fromtimestamp(_stamp("clock.format", timestamp))
        return moment.strftime(pattern)

    def parse(text, pattern):
        expect_string("clock.parse", text)
        expect_string("clock.parse", pattern)

        try:
            return datetime.strptime(text, pattern).timestamp()
        except (ValueError, OSError):
            return None

    def parts(timestamp=None):
        moment = datetime.fromtimestamp(_stamp("clock.parts", timestamp))
        return {
            "year": moment.year,
            "month": moment.month,
            "day": moment.day,
            "hour": moment.hour,
            "minute": moment.minute,
            "second": moment.second,
            "weekday": moment.strftime("%A"),
            "weekday_index": moment.weekday(),
            "yearday": moment.timetuple().tm_yday,
            "timestamp": moment.timestamp(),
        }

    def sleep(seconds):
        expect_number("clock.sleep", seconds)
        time.sleep(seconds)
        return seconds

    def elapsed(start):
        expect_number("clock.elapsed", start)
        return time.time() - start
