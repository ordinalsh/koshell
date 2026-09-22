import glob as glob_module
import os
import shutil
import string
import subprocess
import sys
import tempfile

from koskript import Errors

from . import bridge
from .helpers import expect_array, expect_string, guard


def _entry(path):
    info = os.stat(path)

    return {
        "name": os.path.basename(path),
        "path": path,
        "file": os.path.isfile(path),
        "dir": os.path.isdir(path),
        "link": os.path.islink(path),
        "size": info.st_size,
        "modified": info.st_mtime,
        "created": info.st_ctime,
        "accessed": info.st_atime,
    }


class Filesystem:
    def navigate(path):
        expect_string("filesystem.navigate", path)

        if not os.path.exists(path):
            return False

        with guard("filesystem.navigate"):
            os.chdir(path)

        return True

    def chdir(path):
        return Filesystem.navigate(path)

    def current_dir():
        return os.getcwd()

    def home():
        return os.path.expanduser("~")

    def temp():
        return tempfile.gettempdir()

    def pathjoin(path, *paths):
        expect_string("filesystem.pathjoin", path)

        for part in paths:
            expect_string("filesystem.pathjoin", part)

        return os.path.join(path, *paths)

    def abspath(path):
        expect_string("filesystem.abspath", path)
        return os.path.abspath(path)

    def realpath(path):
        expect_string("filesystem.realpath", path)
        return os.path.realpath(path)

    def normpath(path):
        expect_string("filesystem.normpath", path)
        return os.path.normpath(path)

    def expanduser(path):
        expect_string("filesystem.expanduser", path)
        return os.path.expanduser(path)

    def basename(path):
        expect_string("filesystem.basename", path)
        return os.path.basename(path)

    def dirname(path):
        expect_string("filesystem.dirname", path)
        return os.path.dirname(path)

    def extension(path):
        expect_string("filesystem.extension", path)
        return os.path.splitext(path)[1].lstrip(".")

    def stem(path):
        expect_string("filesystem.stem", path)
        return os.path.splitext(os.path.basename(path))[0]

    def exists(path):
        expect_string("filesystem.exists", path)
        return os.path.exists(path)

    def isfile(path):
        expect_string("filesystem.isfile", path)
        return os.path.isfile(path)

    def isdir(path):
        expect_string("filesystem.isdir", path)
        return os.path.isdir(path)

    def islink(path):
        expect_string("filesystem.islink", path)
        return os.path.islink(path)

    def makedir(path):
        expect_string("filesystem.makedir", path)
        with guard("filesystem.makedir"):
            os.makedirs(path, exist_ok=False)
        return path

    def makedirs(path):
        expect_string("filesystem.makedirs", path)
        with guard("filesystem.makedirs"):
            os.makedirs(path, exist_ok=True)
        return path

    def rmdir(path, verification=False):
        expect_string("filesystem.rmdir", path)

        if not os.path.exists(path):
            return False

        with guard("filesystem.rmdir"):
            if os.listdir(path) and not verification:
                raise Errors.RuntimeError(
                    f"filesystem.rmdir() '{path}' has contents, pass verification=true to confirm its deletion")

            shutil.rmtree(path, ignore_errors=True)

        return True

    def remfile(path):
        expect_string("filesystem.remfile", path)

        if not os.path.exists(path):
            return False

        with guard("filesystem.remfile"):
            os.remove(path)

        return True

    def remove(path):
        return Filesystem.remfile(path)

    def rename(source, destination):
        expect_string("filesystem.rename", source)
        expect_string("filesystem.rename", destination)
        with guard("filesystem.rename"):
            os.replace(source, destination)
        return destination

    def copy(source, destination):
        expect_string("filesystem.copy", source)
        expect_string("filesystem.copy", destination)
        with guard("filesystem.copy"):
            shutil.copy2(source, destination)
        return destination

    def copytree(source, destination):
        expect_string("filesystem.copytree", source)
        expect_string("filesystem.copytree", destination)
        with guard("filesystem.copytree"):
            shutil.copytree(source, destination)
        return destination

    def move(source, destination):
        expect_string("filesystem.move", source)
        expect_string("filesystem.move", destination)
        with guard("filesystem.move"):
            return shutil.move(source, destination)

    def touch(path):
        expect_string("filesystem.touch", path)
        with guard("filesystem.touch"):
            with open(path, "w", encoding="utf-8") as file:
                file.write("")
        return True

    def read(path, encoding="utf-8"):
        expect_string("filesystem.read", path)
        with guard("filesystem.read", UnicodeDecodeError):
            with open(path, "r", encoding=encoding) as file:
                return file.read()

    def write(path, text, append=False, encoding="utf-8"):
        expect_string("filesystem.write", path)
        expect_string("filesystem.write", text)
        mode = "a" if append else "w"
        with guard("filesystem.write"):
            with open(path, mode, encoding=encoding) as file:
                file.write(text)
        return path

    def readlines(path, encoding="utf-8"):
        expect_string("filesystem.readlines", path)
        with guard("filesystem.readlines", UnicodeDecodeError):
            with open(path, "r", encoding=encoding) as file:
                return file.read().splitlines()

    def writelines(path, lines, append=False, encoding="utf-8"):
        expect_array("filesystem.writelines", lines)
        mode = "a" if append else "w"
        with guard("filesystem.writelines"):
            with open(path, mode, encoding=encoding) as file:
                for line in lines:
                    file.write(f"{line}\n")
        return path

    def listdir(path):
        expect_string("filesystem.listdir", path)

        if not os.path.exists(path):
            return False

        with guard("filesystem.listdir"):
            return sorted(os.listdir(path))

    def entries(path):
        expect_string("filesystem.entries", path)
        with guard("filesystem.entries"):
            return [_entry(os.path.join(path, name)) for name in sorted(os.listdir(path))]

    def walk(path, callback=None):
        expect_string("filesystem.walk", path)

        if not os.path.exists(path):
            raise Errors.RuntimeError(f"filesystem.walk() path does not exist: {path}")

        results = []

        with guard("filesystem.walk"):
            for root, dirs, files in os.walk(path):
                for name in sorted(dirs) + sorted(files):
                    entry = _entry(os.path.join(root, name))
                    results.append(entry)
                    bridge.call(callback, entry)

        return results

    def glob(path, pattern):
        expect_string("filesystem.glob", path)
        expect_string("filesystem.glob", pattern)
        with guard("filesystem.glob"):
            return sorted(glob_module.glob(os.path.join(path, pattern), recursive=True))

    def find(path, pattern):
        return Filesystem.glob(path, pattern)

    def size(path):
        expect_string("filesystem.size", path)
        with guard("filesystem.size"):
            return os.path.getsize(path)

    def modified(path):
        expect_string("filesystem.modified", path)
        with guard("filesystem.modified"):
            return os.path.getmtime(path)

    def created(path):
        expect_string("filesystem.created", path)
        with guard("filesystem.created"):
            return os.path.getctime(path)

    def accessed(path):
        expect_string("filesystem.accessed", path)
        with guard("filesystem.accessed"):
            return os.path.getatime(path)

    def disk(path="."):
        expect_string("filesystem.disk", path)
        with guard("filesystem.disk"):
            usage = shutil.disk_usage(path)
        percent = round(usage.used / usage.total * 100, 2)
        return {
            "path": os.path.abspath(path),
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": percent,
        }

    def drives():
        if os.name == "nt":
            found = []
            for letter in string.ascii_uppercase:
                root = f"{letter}:\\"
                if os.path.exists(root):
                    found.append(root)
            return found

        return ["/"]

    def mktemp(prefix="koshell-", suffix=".tmp"):
        expect_string("filesystem.mktemp", prefix)
        expect_string("filesystem.mktemp", suffix)
        with guard("filesystem.mktemp"):
            descriptor, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
            os.close(descriptor)
        return path

    def open(path):
        expect_string("filesystem.open", path)

        if not os.path.exists(path):
            raise Errors.RuntimeError(f"filesystem.open() path does not exist: {path}")

        try:
            if hasattr(os, "startfile"):
                os.startfile(path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.Popen([opener, path])
        except OSError as error:
            raise Errors.RuntimeError(f"filesystem.open() failed: {error}") from None

        return True
