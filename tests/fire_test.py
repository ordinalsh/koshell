import functools
import inspect
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import traceback
import warnings
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from koskript import Errors, KoskriptRuntime
from rich.console import Console

import standard.filesystem as filesystem_module
import standard.input as input_module
import standard.output as output_module
import standard.system as system_module
from standard import MODULES as MODULE_CLASSES
from standard import execution_lock, register_standard

KOSKRIPT_ERRORS = (
    Errors.SyntaxError,
    Errors.NameError,
    Errors.MismatchType,
    Errors.ProtectedObject,
    Errors.RuntimeError,
)

NATIVE = (type(None), bool, int, float, str, list, dict)

CHECKS = 0
PASSED = 0
COVERED = set()
FAILURES = []
THREAD_ERRORS = []
LOGS = []
INPUT_QUEUE = []
OPENED = []
CHILDREN = []

LOGS_LOCK = threading.Lock()


def expect(condition, message=""):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(message or "expectation failed")


def expect_equal(value, expected, message=""):
    expect(value == expected, f"{message}: {value!r} != {expected!r}")


def expect_native(value, message=""):
    expect(isinstance(value, NATIVE), f"{message}: non-native return {type(value).__name__}")
    if isinstance(value, list):
        for item in value:
            expect_native(item, message)
    elif isinstance(value, dict):
        for item in value.values():
            expect_native(item, message)


def expect_raises(error_type, function, *args):
    try:
        function(*args)
    except error_type as error:
        global CHECKS
        CHECKS += 1
        return error
    except Exception as error:
        raise AssertionError(
            f"expected {error_type.__name__}, got {type(error).__name__}: {error}") from None
    raise AssertionError(f"expected {error_type.__name__}, nothing was raised")


runtime = KoskriptRuntime()
runtime.register("print", lambda *args: LOGS.append(" ".join(str(a) for a in args)))
register_standard(runtime)

MODULES = {name: runtime[name] for name in MODULE_CLASSES}
KOSHELL = runtime["koshell"]


def recorder(module_name, function_name, function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        COVERED.add(f"{module_name}.{function_name}")
        return function(*args, **kwargs)
    return wrapper


def instrument(module_name, target):
    for name in list(vars(target)):
        value = getattr(target, name)
        if name.startswith("_") or not callable(value):
            continue
        setattr(target, name, recorder(module_name, name, value))


for module_name, target in MODULES.items():
    instrument(module_name, target)

instrument("koshell", type(KOSHELL))


def call(module, function, *args):
    target = KOSHELL if module == "koshell" else MODULES[module]
    return getattr(target, function)(*args)


def run_script(code):
    with execution_lock():
        return runtime.execute(code)


def public_functions(target):
    owner = target if isinstance(target, type) else type(target)
    return [
        name for name in vars(owner)
        if not name.startswith("_") and callable(getattr(target, name))
    ]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_payload(self, payload, status=200, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_all(self):
        if self.path.startswith("/slow"):
            time.sleep(1.5)

        if self.path.startswith("/file.bin"):
            self.send_payload(b"koshell-binary" * 64, content_type="application/octet-stream")
            return

        if self.path.startswith("/script.kos"):
            self.send_payload(b'print("remoto")\n40 + 2', content_type="text/plain")
            return

        if self.path.startswith("/data.json"):
            self.send_payload({"name": "koshell", "tags": ["a", "b"], "n": 3})
            return

        if self.path.startswith("/status/"):
            code = int(self.path.split("/")[2].split("?")[0])
            self.send_payload({"status": code}, status=code)
            return

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode() if length else ""
        self.send_payload({
            "method": self.command,
            "path": self.path,
            "body": body,
            "header": self.headers.get("X-Test", ""),
        })

    do_GET = handle_all
    do_POST = handle_all
    do_PUT = handle_all
    do_PATCH = handle_all
    do_DELETE = handle_all

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()


server = HTTPServer(("127.0.0.1", 0), Handler)
PORT = server.server_address[1]
BASE = f"http://127.0.0.1:{PORT}"
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

WORK = tempfile.mkdtemp(prefix="koshell-fire-")
SANDBOX = os.path.join(WORK, "sandbox")
os.makedirs(SANDBOX)
runtime.register("work", SANDBOX)
ENV_SNAPSHOT = dict(os.environ)
ORIGINAL_CONSOLE = output_module.Output.console
ORIGINAL_PROMPT = input_module.Prompt
ORIGINAL_CONFIRM = input_module.Confirm
ORIGINAL_INTPROMPT = input_module.IntPrompt
ORIGINAL_THREAD_HOOK = threading.excepthook
BUFFER = io.StringIO()


def path(*parts):
    return os.path.join(SANDBOX, *parts)


class FakePrompt:
    @staticmethod
    def ask(prompt, default=None, password=False, choices=None):
        value = INPUT_QUEUE.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value


def thread_hook(args):
    THREAD_ERRORS.append(f"{args.thread.name}: {args.exc_type.__name__}: {args.exc_value}")


def test_harness():
    expect_equal(sorted(MODULES.keys()), sorted(MODULE_CLASSES.keys()))
    expect_equal(len(MODULES), 13)
    expect_equal(getattr(KOSHELL, "version"), "2.1.0")
    expect_equal(run_script("1 + 1"), 2)
    expect_equal(run_script('"a" + "b"'), "ab")


def test_filesystem_paths():
    expect_equal(call("filesystem", "current_dir"), os.getcwd())
    expect(os.path.isdir(call("filesystem", "home")))
    expect(os.path.isdir(call("filesystem", "temp")))
    expect(isinstance(call("filesystem", "drives"), list))
    expect_equal(call("filesystem", "pathjoin", "a", "b", "c"), os.path.join("a", "b", "c"))
    expect_equal(call("filesystem", "abspath", "x"), os.path.abspath("x"))
    expect_equal(call("filesystem", "realpath", "x"), os.path.realpath("x"))
    expect_equal(call("filesystem", "normpath", "a/../b"), os.path.normpath("a/../b"))
    expect(call("filesystem", "expanduser", "~").startswith(os.path.expanduser("~")))
    expect_equal(call("filesystem", "basename", os.path.join("a", "b.txt")), "b.txt")
    expect_equal(call("filesystem", "dirname", os.path.join("a", "b.txt")), "a")
    expect_equal(call("filesystem", "extension", "a/b/c.tar.gz"), "gz")
    expect_equal(call("filesystem", "extension", "sin_extension"), "")
    expect_equal(call("filesystem", "stem", "a/b/c.tar.gz"), "c.tar")
    expect_native(call("filesystem", "pathjoin", "a", "b"))
    expect_raises(Errors.MismatchType, call, "filesystem", "pathjoin", 1, "b")
    expect_raises(Errors.MismatchType, call, "filesystem", "pathjoin", "a", 1)
    expect_raises(Errors.MismatchType, call, "filesystem", "abspath", None)
    expect_raises(Errors.MismatchType, call, "filesystem", "basename", 1)
    expect_raises(Errors.MismatchType, call, "filesystem", "stem", 1)


def test_filesystem_queries():
    file_path = path("query.txt")
    call("filesystem", "write", file_path, "contenido")

    expect_equal(call("filesystem", "exists", file_path), True)
    expect_equal(call("filesystem", "exists", path("nope.txt")), False)
    expect_equal(call("filesystem", "isfile", file_path), True)
    expect_equal(call("filesystem", "isdir", file_path), False)
    expect_equal(call("filesystem", "isdir", SANDBOX), True)
    expect_equal(call("filesystem", "islink", file_path), False)
    expect_equal(call("filesystem", "size", file_path), len("contenido"))
    expect(call("filesystem", "modified", file_path) > 0)
    expect(call("filesystem", "created", file_path) > 0)
    expect(call("filesystem", "accessed", file_path) > 0)

    disk = call("filesystem", "disk", SANDBOX)
    expect(disk["total"] > 0 and disk["free"] >= 0)
    expect(0 <= disk["percent"] <= 100)
    expect_native(disk, "filesystem.disk")

    expect_raises(Errors.RuntimeError, call, "filesystem", "size", path("nope.txt"))
    expect_raises(Errors.RuntimeError, call, "filesystem", "modified", path("nope.txt"))
    expect_raises(Errors.RuntimeError, call, "filesystem", "disk", path("nope-dir"))
    expect_raises(Errors.MismatchType, call, "filesystem", "exists", None)

    link = path("link.txt")
    try:
        os.symlink(file_path, link)
        expect_equal(call("filesystem", "islink", link), True)
    except (OSError, NotImplementedError):
        expect(True)


def test_filesystem_directories():
    expect_equal(call("filesystem", "navigate", path("nope-dir")), False)
    expect_equal(call("filesystem", "chdir", path("nope-dir")), False)

    created = path("dirs", "deep")
    expect_equal(call("filesystem", "makedir", path("dirs")), path("dirs"))
    expect_equal(call("filesystem", "makedirs", created), created)
    expect(os.path.isdir(created))
    expect_raises(Errors.RuntimeError, call, "filesystem", "makedir", path("dirs"))
    expect_equal(call("filesystem", "makedirs", path("dirs")), path("dirs"))

    call("filesystem", "write", os.path.join(created, "f.txt"), "x")
    expect_equal(call("filesystem", "listdir", path("dirs")), ["deep"])
    expect_equal(call("filesystem", "listdir", path("nope-dir")), False)
    expect_raises(Errors.RuntimeError, call, "filesystem", "listdir", path("query.txt"))

    entries = call("filesystem", "entries", path("dirs"))
    expect_equal(len(entries), 1)
    expect_equal(entries[0]["name"], "deep")
    expect_equal(entries[0]["dir"], True)
    expect_native(entries, "filesystem.entries")

    walked = call("filesystem", "walk", path("dirs"))
    expect_equal(len(walked), 2)
    collected = []
    call("filesystem", "walk", path("dirs"), collected.append)
    expect_equal(len(collected), 2)
    expect_raises(Errors.RuntimeError, call, "filesystem", "walk", path("nope-dir"))
    expect_raises(Errors.RuntimeError, call, "filesystem", "entries", path("nope-dir"))

    expect_raises(Errors.RuntimeError, call, "filesystem", "rmdir", path("dirs"))
    expect_equal(call("filesystem", "rmdir", path("dirs"), True), True)
    expect_equal(call("filesystem", "rmdir", path("dirs")), False)
    expect_equal(call("filesystem", "rmdir", path("nope-dir")), False)

    original = os.getcwd()
    expect_equal(call("filesystem", "navigate", SANDBOX), True)
    expect_equal(call("filesystem", "current_dir"), SANDBOX)
    expect_equal(call("filesystem", "chdir", original), True)
    expect_raises(Errors.RuntimeError, call, "filesystem", "navigate", path("query.txt"))
    expect_raises(Errors.RuntimeError, call, "filesystem", "chdir", path("query.txt"))


def test_filesystem_files():
    expect_equal(call("filesystem", "touch", path("touch.txt")), True)
    expect_equal(call("filesystem", "read", path("touch.txt")), "")

    target = path("write.txt")
    expect_equal(call("filesystem", "write", target, "uno\n"), target)
    call("filesystem", "write", target, "dos\n", True)
    expect_equal(call("filesystem", "read", target), "uno\ndos\n")
    expect_equal(call("filesystem", "readlines", target), ["uno", "dos"])
    expect_equal(call("filesystem", "write", target, "tres\n"), target)
    expect_equal(call("filesystem", "read", target), "tres\n")

    lines = path("lines.txt")
    expect_equal(call("filesystem", "writelines", lines, ["a", "b"]), lines)
    call("filesystem", "writelines", lines, ["c"], True)
    expect_equal(call("filesystem", "readlines", lines), ["a", "b", "c"])

    expect_equal(call("filesystem", "copy", target, path("copy.txt")), path("copy.txt"))
    expect_equal(call("filesystem", "read", path("copy.txt")), "tres\n")
    expect_equal(call("filesystem", "rename", path("copy.txt"), path("renamed.txt")), path("renamed.txt"))
    expect_equal(call("filesystem", "move", path("renamed.txt"), path("moved.txt")), path("moved.txt"))
    expect_equal(call("filesystem", "exists", path("moved.txt")), True)

    tree = path("tree-src")
    os.makedirs(os.path.join(tree, "sub"))
    call("filesystem", "write", os.path.join(tree, "sub", "x.txt"), "x")
    expect_equal(call("filesystem", "copytree", tree, path("tree-copy")), path("tree-copy"))
    expect_equal(call("filesystem", "exists", os.path.join(path("tree-copy"), "sub", "x.txt")), True)

    expect_equal(call("filesystem", "remfile", path("moved.txt")), True)
    expect_equal(call("filesystem", "remfile", path("moved.txt")), False)
    expect_equal(call("filesystem", "remove", path("copy.txt")), False)
    expect_equal(call("filesystem", "remove", path("lines.txt")), True)

    temp_path = call("filesystem", "mktemp", "fire-", ".tmp")
    expect(os.path.exists(temp_path))
    os.remove(temp_path)

    opened = []
    if hasattr(os, "startfile"):
        original_startfile = os.startfile
        os.startfile = lambda target: opened.append(target)
    else:
        original_popen = filesystem_module.subprocess.Popen
        filesystem_module.subprocess.Popen = lambda *args, **kwargs: opened.append(args)

    try:
        expect_equal(call("filesystem", "open", target), True)
        expect_equal(len(opened), 1)
        expect_raises(Errors.RuntimeError, call, "filesystem", "open", path("nope.txt"))
    finally:
        if hasattr(os, "startfile"):
            os.startfile = original_startfile
        else:
            filesystem_module.subprocess.Popen = original_popen

    expect_raises(Errors.RuntimeError, call, "filesystem", "read", path("nope.txt"))
    expect_raises(Errors.RuntimeError, call, "filesystem", "read", SANDBOX)
    expect_raises(Errors.RuntimeError, call, "filesystem", "write", path("no-dir", "f.txt"), "x")
    expect_raises(Errors.RuntimeError, call, "filesystem", "touch", SANDBOX)
    expect_raises(Errors.RuntimeError, call, "filesystem", "remfile", SANDBOX)
    expect_raises(Errors.RuntimeError, call, "filesystem", "copy", path("nope.txt"), path("x.txt"))
    expect_raises(Errors.MismatchType, call, "filesystem", "write", target, 1)
    expect_raises(Errors.MismatchType, call, "filesystem", "writelines", target, "no-array")


def test_filesystem_search():
    os.makedirs(path("search", "sub"), exist_ok=True)
    call("filesystem", "write", path("search", "a.txt"), "a")
    call("filesystem", "write", path("search", "sub", "b.txt"), "b")
    call("filesystem", "write", path("search", "sub", "c.md"), "c")

    found = call("filesystem", "glob", path("search"), "**/*.txt")
    expect_equal(len(found), 2)
    expect_equal(found, call("filesystem", "find", path("search"), "**/*.txt"))
    expect_equal(call("filesystem", "glob", path("search"), "*.md"), [])
    expect_equal(call("filesystem", "glob", path("nope-dir"), "*"), [])
    expect_raises(Errors.MismatchType, call, "filesystem", "glob", path("search"), None)


def test_process():
    tasks = call("process", "get_tasks")
    expect(len(tasks) > 0)
    expect_native(tasks, "process.get_tasks")
    for task in tasks:
        expect(set(["pid", "name", "status", "memory", "memory_human", "threads", "created", "user"]) <= set(task.keys()))

    expect_equal(call("process", "pid"), os.getpid())
    expect_equal(call("process", "exists", os.getpid()), True)
    expect_equal(call("process", "exists", 99999999), False)

    me = call("process", "info", os.getpid())
    expect_equal(me["pid"], os.getpid())
    expect_equal(call("process", "info", 99999999), None)
    expect_equal(call("process", "parent", 99999999), None)
    expect_equal(call("process", "children", 99999999), [])
    expect_equal(call("process", "cmdline", 99999999), [])
    expect_equal(call("process", "cwd", 99999999), None)
    expect_equal(call("process", "wait", 99999999), False)

    expect(call("process", "find", "python") is not None)
    expect_equal(len(call("process", "find", "no-such-process-xyz")), 0)

    top_memory = call("process", "top", 3)
    expect_equal(len(top_memory), 3)
    expect(top_memory[0]["memory"] >= top_memory[-1]["memory"])
    top_cpu = call("process", "top", 3, "cpu")
    expect_equal(len(top_cpu), 3)
    expect("cpu" in top_cpu[0])
    expect_raises(Errors.MismatchType, call, "process", "top", 3, "nope")

    expect(call("process", "which", os.path.basename(sys.executable)) is not None)
    expect_equal(call("process", "which", "definitely-not-real-koshell-xyz"), None)

    echo = call("process", "run", "echo koshell-fire")
    expect(echo["ok"] and "koshell-fire" in echo["stdout"])
    expect_equal(echo["code"], 0)
    expect(echo["duration"] >= 0)

    direct = call("process", "run", [sys.executable, "-c", "print('directo')"])
    expect_equal(direct["stdout"].strip(), "directo")

    missing = call("process", "run", "definitely-not-real-koshell-xyz")
    expect_equal(missing["ok"], False)

    expect_raises(Errors.RuntimeError, call, "process", "run",
                  [sys.executable, "-c", "import time; time.sleep(5)"], None, 0.3)
    expect_raises(Errors.RuntimeError, call, "process", "run", "echo", path("nope-dir"))
    expect_raises(Errors.MismatchType, call, "process", "run", None)
    expect_raises(Errors.MismatchType, call, "process", "run", "echo", None, "x")

    child = call("process", "spawn", [sys.executable, "-c", "import time; time.sleep(30)"])
    CHILDREN.append(child)
    time.sleep(0.6)

    expect_equal(call("process", "exists", child), True)
    child_info = call("process", "info", child)
    expect(child_info["name"].lower().startswith("python"))
    expect_equal(call("process", "parent", child)["pid"], os.getpid())
    expect(any(task["pid"] == child for task in call("process", "children", os.getpid())))
    expect(any("python" in part.lower() for part in call("process", "cmdline", child)))
    expect(call("process", "cwd", child) is not None)

    expect_equal(call("process", "wait", child, 0.2), False)
    expect_equal(call("process", "suspend", child), True)
    expect_equal(call("process", "resume", child), True)
    expect_equal(call("process", "terminate_task", child), True)
    expect_equal(call("process", "wait", child, 5), True)
    CHILDREN.remove(child)

    doomed = call("process", "spawn", [sys.executable, "-c", "import time; time.sleep(30)"])
    CHILDREN.append(doomed)
    time.sleep(0.4)
    expect_equal(call("process", "kill_task", doomed), True)
    expect_equal(call("process", "wait", doomed, 5), True)
    CHILDREN.remove(doomed)

    expect_equal(call("process", "terminate_task", 99999999), False)
    expect_equal(call("process", "kill_task", 99999999), False)
    expect_equal(call("process", "suspend", 99999999), False)
    expect_equal(call("process", "resume", 99999999), False)
    expect_raises(Errors.MismatchType, call, "process", "info", None)
    expect_raises(Errors.MismatchType, call, "process", "exists", None)


def test_env():
    try:
        expect_equal(call("env", "set", "KOSHELL_FIRE", "si"), "si")
        expect_equal(call("env", "get", "KOSHELL_FIRE"), "si")
        expect_equal(call("env", "has", "KOSHELL_FIRE"), True)
        expect_equal(call("env", "get", "KOSHELL_FIRE_NOPE", "defecto"), "defecto")
        expect_equal(call("env", "get", "KOSHELL_FIRE_NOPE"), None)
        expect_equal(call("env", "has", "KOSHELL_FIRE_NOPE"), False)
        expect_equal(call("env", "expand", "$KOSHELL_FIRE"), "si")
        expect("KOSHELL_FIRE" in call("env", "all"))
        expect(len(call("env", "path")) > 0)
        expect_native(call("env", "all"), "env.all")

        expect_equal(call("env", "add_path", "C:\\koshell-fire" if os.name == "nt" else "/koshell-fire"),
                     "C:\\koshell-fire" if os.name == "nt" else "/koshell-fire")
        expect(("C:\\koshell-fire" if os.name == "nt" else "/koshell-fire") in call("env", "path"))
        call("env", "remove_path", "C:\\koshell-fire" if os.name == "nt" else "/koshell-fire")
        expect(("C:\\koshell-fire" if os.name == "nt" else "/koshell-fire") not in call("env", "path"))

        expect_equal(call("env", "unset", "KOSHELL_FIRE"), True)
        expect_equal(call("env", "unset", "KOSHELL_FIRE"), False)
        expect_equal(call("env", "has", "KOSHELL_FIRE"), False)

        expect_raises(Errors.MismatchType, call, "env", "get", None)
        expect_raises(Errors.MismatchType, call, "env", "set", "x", 1)
    finally:
        os.environ.clear()
        os.environ.update(ENV_SNAPSHOT)


def test_system():
    expect(isinstance(call("system", "platform"), str) and len(call("system", "platform")) > 0)
    expect(isinstance(call("system", "release"), str))
    expect(isinstance(call("system", "version"), str))
    expect(isinstance(call("system", "machine"), str))
    expect(isinstance(call("system", "hostname"), str) and len(call("system", "hostname")) > 0)
    expect(isinstance(call("system", "user"), str) and len(call("system", "user")) > 0)
    expect(os.path.isdir(call("system", "home")))
    expect(call("system", "python").startswith("3."))

    expect(call("system", "cpu_count") >= 1)
    expect(call("system", "cpu_count", False) >= 1)
    expect(0 <= call("system", "cpu_percent", 0.05) <= 100)

    memory = call("system", "memory")
    expect(memory["total"] > 0 and memory["used"] >= 0 and memory["percent"] >= 0)
    expect(memory["total_human"].endswith(("B", "KB", "MB", "GB", "TB")))
    expect_native(memory, "system.memory")

    swap = call("system", "swap")
    expect(swap["total"] >= 0 and swap["percent"] >= 0)

    disk = call("system", "disk", SANDBOX)
    expect(disk["total"] > 0 and disk["free_human"].endswith(("B", "KB", "MB", "GB", "TB")))

    expect(call("system", "boot_time") < time.time())
    expect(call("system", "uptime") > 0)
    expect(isinstance(call("system", "locale"), str))
    expect(isinstance(call("system", "timezone"), str))

    info = call("system", "info")
    expect(set(["platform", "hostname", "user", "python", "cpu_count", "memory", "disk", "uptime"]) <= set(info.keys()))
    expect_native(info, "system.info")

    opened = []
    if hasattr(os, "startfile"):
        original_startfile = os.startfile
        os.startfile = lambda target: opened.append(target)
    else:
        original_popen = system_module.subprocess.Popen
        system_module.subprocess.Popen = lambda *args, **kwargs: opened.append(args)

    try:
        expect_equal(call("system", "open", SANDBOX), True)
        expect_equal(len(opened), 1)
        expect_raises(Errors.RuntimeError, call, "system", "open", path("nope.txt"))
    finally:
        if hasattr(os, "startfile"):
            os.startfile = original_startfile
        else:
            system_module.subprocess.Popen = original_popen

    expect_raises(Errors.MismatchType, call, "system", "disk", None)
    expect_raises(Errors.MismatchType, call, "system", "cpu_percent", "x")


def test_clock():
    now = call("clock", "now")
    expect(isinstance(now, float) and now > 0)
    expect(isinstance(call("clock", "utc_now"), float))

    stamp = call("clock", "parse", "2024-01-02 03:04:05", "%Y-%m-%d %H:%M:%S")
    expect(isinstance(stamp, float))
    expect_equal(call("clock", "parse", "nope", "%Y"), None)
    expect_equal(call("clock", "parse", "x", "x"), None)

    expect("T" in call("clock", "iso", stamp))
    expect(call("clock", "utc_iso", stamp).endswith("+00:00"))
    expect_equal(call("clock", "date", stamp), "2024-01-02")
    expect_equal(call("clock", "time", stamp), "03:04:05")
    expect_equal(call("clock", "format", stamp, "%Y"), "2024")
    expect_equal(call("clock", "weekday", stamp), time.strftime("%A", time.localtime(stamp)))

    parts = call("clock", "parts", stamp)
    expect_equal(parts["year"], 2024)
    expect_equal(parts["month"], 1)
    expect_equal(parts["day"], 2)
    expect_equal(parts["hour"], 3)
    expect_equal(parts["minute"], 4)
    expect_equal(parts["second"], 5)
    expect_equal(parts["weekday_index"], 1)
    expect_native(parts, "clock.parts")

    expect_equal(call("clock", "sleep", 0.02), 0.02)
    expect(call("clock", "elapsed", now - 1) >= 0.9)
    expect_raises(Errors.MismatchType, call, "clock", "format", None, None)
    expect_raises(Errors.MismatchType, call, "clock", "sleep", "x")
    expect_raises(Errors.MismatchType, call, "clock", "iso", "x")


def test_network():
    response = call("network", "get", BASE)
    expect_equal(response["status"], 200)
    expect_equal(response["ok"], True)
    expect_equal(response["reason"], "OK")
    expect("GET" in response["text"])
    expect(response["url"].startswith(BASE))
    expect(isinstance(response["headers"], dict))
    expect(response["elapsed"] >= 0)
    expect_native(response, "network.get")

    expect_equal(call("network", "get", BASE + "/status/404")["ok"], False)
    expect_equal(call("network", "get", BASE + "/status/500")["status"], 500)

    posted = call("network", "post", BASE, {"a": 1, "b": "dos"})
    expect("a=1" in posted["text"] and "b=dos" in posted["text"])
    expect('"method": "POST"' in posted["text"])

    payload = call("network", "post", BASE, None, {"x": 1, "y": [1, 2]})
    expect('\\"x\\": 1' in payload["text"])
    expect('\\"y\\": [1, 2]' in payload["text"])

    expect("PUT" in call("network", "put", BASE, "cuerpo")["text"])
    expect("PATCH" in call("network", "patch", BASE, "cuerpo")["text"])
    expect("DELETE" in call("network", "delete", BASE)["text"])
    expect_equal(call("network", "head", BASE)["status"], 200)

    requested = call("network", "request", "GET", BASE, {"X-Test": "si"}, {"q": "1"}, None, None, 10)
    expect_equal(requested["status"], 200)
    expect("q=1" in requested["text"])
    expect('"header": "si"' in requested["text"])
    expect_equal(call("network", "request", "POST", BASE + "/status/201")["status"], 201)

    data = call("network", "get_json", BASE + "/data.json")
    expect_equal(data["name"], "koshell")
    expect_equal(data["tags"], ["a", "b"])

    posted_json = call("network", "post_json", BASE, {"ok": True})
    expect_equal(posted_json["method"], "POST")
    expect_raises(Errors.RuntimeError, call, "network", "get_json", BASE + "/file.bin")

    target = path("download.bin")
    downloaded = call("network", "download", BASE + "/file.bin", target, 10)
    expect_equal(downloaded["ok"], True)
    expect(downloaded["size"] > 0)
    expect_equal(downloaded["path"], target)
    expect_equal(os.path.getsize(target), downloaded["size"])

    expect_equal(call("network", "resolve", "127.0.0.1"), "127.0.0.1")
    expect_equal(call("network", "resolve", "definitely-not-real-koshell.invalid"), None)
    expect_equal(call("network", "local_ip") != "", True)
    expect_equal(call("network", "is_online", "127.0.0.1", PORT, 2), True)
    expect_equal(call("network", "is_online", "127.0.0.1", 59999, 0.2), False)
    expect_equal(call("network", "port_open", "127.0.0.1", PORT, 2), True)
    expect_equal(call("network", "port_open", "127.0.0.1", 59999, 0.2), False)

    public = call("network", "public_ip", 3)
    expect(public is None or isinstance(public, str))

    expect_raises(Errors.RuntimeError, call, "network", "get", BASE + "/slow", None, 0.2)
    expect_raises(Errors.RuntimeError, call, "network", "get", "not-a-url")
    expect_raises(Errors.RuntimeError, call, "network", "download", BASE + "/status/404", path("nope.bin"), 5)
    expect_raises(Errors.MismatchType, call, "network", "get", None)
    expect_raises(Errors.MismatchType, call, "network", "get", BASE, None, "x")
    expect_raises(Errors.MismatchType, call, "network", "post", BASE, 5)


def test_archive():
    source = path("arc-src")
    os.makedirs(os.path.join(source, "sub"), exist_ok=True)
    call("filesystem", "write", os.path.join(source, "one.txt"), "uno")
    call("filesystem", "write", os.path.join(source, "sub", "two.txt"), "dos")

    zip_path = path("pack.zip")
    created = call("archive", "zip_create", zip_path, source)
    expect_equal(created["entries"], 2)
    expect_equal(created["path"], zip_path)

    listing = call("archive", "zip_list", zip_path)
    names = [entry["name"] for entry in listing]
    expect("arc-src/one.txt" in names and "arc-src/sub/two.txt" in names)
    expect(listing[0]["size"] > 0)
    expect_native(listing, "archive.zip_list")

    expect_equal(call("archive", "contains", zip_path, "arc-src/one.txt"), True)
    expect_equal(call("archive", "contains", zip_path, "nope.txt"), False)
    expect_equal(call("archive", "read", zip_path, "arc-src/one.txt"), "uno")
    expect_raises(Errors.RuntimeError, call, "archive", "read", zip_path, "nope.txt")

    extra = path("extra.txt")
    call("filesystem", "write", extra, "extra")
    added = call("archive", "zip_add", zip_path, [extra])
    expect_equal(added["entries"], 1)
    expect_equal(call("archive", "contains", zip_path, "extra.txt"), True)

    out = path("unzip")
    extracted = call("archive", "zip_extract", zip_path, out)
    expect("arc-src/one.txt" in extracted)
    expect_equal(call("filesystem", "read", os.path.join(out, "arc-src", "one.txt")), "uno")

    call("archive", "zip_create", path("stored.zip"), source, "stored")
    expect_raises(Errors.MismatchType, call, "archive", "zip_create", path("bad.zip"), source, "nope")

    tar_path = path("pack.tar.gz")
    created_tar = call("archive", "tar_create", tar_path, source)
    expect_equal(created_tar["entries"], 2)
    expect_equal(len(call("archive", "tar_list", tar_path)), 2)
    expect_equal(call("archive", "tar_list", tar_path)[0]["compressed"], None)

    tar_out = path("untar")
    call("archive", "tar_extract", tar_path, tar_out)
    expect_equal(call("filesystem", "read", os.path.join(tar_out, "arc-src", "sub", "two.txt")), "dos")

    call("archive", "tar_create", path("plain.tar"), source, "none")
    call("archive", "tar_create", path("bz.tar.bz2"), source)
    call("archive", "tar_create", path("xz.tar.xz"), source)
    expect_raises(Errors.MismatchType, call, "archive", "tar_create", path("bad.tar"), source, "rar")

    call("archive", "pack", path("packed.zip"), source)
    call("archive", "pack", path("packed.tar.gz"), source)
    expect_equal(len(call("archive", "unpack", path("packed.zip"), path("unpacked"))), 2)
    expect_raises(Errors.RuntimeError, call, "archive", "pack", path("packed.rar"), source)
    expect_raises(Errors.RuntimeError, call, "archive", "unpack", path("extra.txt"), path("nope"))

    expect_raises(Errors.RuntimeError, call, "archive", "zip_list", extra)
    expect_raises(Errors.RuntimeError, call, "archive", "zip_extract", extra, path("nope"))
    expect_raises(Errors.RuntimeError, call, "archive", "tar_list", extra)
    expect_raises(Errors.RuntimeError, call, "archive", "tar_extract", extra, path("nope"))
    expect_raises(Errors.RuntimeError, call, "archive", "contains", extra, "x")
    expect_raises(Errors.RuntimeError, call, "archive", "read", extra, "x")
    expect_raises(Errors.MismatchType, call, "archive", "zip_create", None, source)

    missing_zip = path("nope.zip")
    missing_tar = path("nope.tar")
    expect_raises(Errors.RuntimeError, call, "archive", "zip_list", missing_zip)
    expect_raises(Errors.RuntimeError, call, "archive", "zip_extract", missing_zip, path("nope-out"))
    appended = path("appended.zip")
    expect_equal(call("archive", "zip_add", appended, extra)["entries"], 1)
    expect_equal(call("archive", "contains", appended, "extra.txt"), True)
    expect_raises(Errors.RuntimeError, call, "archive", "tar_list", missing_tar)
    expect_raises(Errors.RuntimeError, call, "archive", "tar_extract", missing_tar, path("nope-out"))
    expect_raises(Errors.RuntimeError, call, "archive", "contains", missing_zip, "x")
    expect_raises(Errors.RuntimeError, call, "archive", "read", missing_zip, "x")
    expect_raises(Errors.RuntimeError, call, "archive", "unpack", missing_zip, path("nope-out"))
    expect_raises(Errors.RuntimeError, call, "archive", "zip_create", path("nope-out.zip"), path("nope-src"))
    expect_raises(Errors.RuntimeError, call, "archive", "tar_create", path("nope-out.tar"), path("nope-src"))
    expect_raises(Errors.RuntimeError, call, "archive", "pack", path("nope-src.zip"), path("nope-src"))


def test_codec():
    expect_equal(call("codec", "base64_encode", "hola"), "aG9sYQ==")
    expect_equal(call("codec", "base64_decode", "aG9sYQ=="), "hola")
    expect_equal(call("codec", "base64_url_encode", "hola?"), "aG9sYT8=")
    expect_equal(call("codec", "base64_url_decode", "aG9sYT8="), "hola?")
    expect_equal(call("codec", "hex_encode", "hi"), "6869")
    expect_equal(call("codec", "hex_decode", "6869"), "hi")
    expect_equal(call("codec", "url_encode", "a b&c"), "a%20b%26c")
    expect_equal(call("codec", "url_decode", "a%20b%26c"), "a b&c")

    expect_equal(call("codec", "hash", "abc"),
                 "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    expect_equal(len(call("codec", "hash", "abc", "md5")), 32)
    expect_equal(len(call("codec", "hash", "abc", "sha512")), 128)
    expect_equal(call("codec", "hash", "abc"), call("codec", "hash", "abc", "sha256"))

    file_path = path("hash.txt")
    call("filesystem", "write", file_path, "abc")
    expect_equal(call("codec", "hash_file", file_path), call("codec", "hash", "abc"))

    signature = call("codec", "sign", "mensaje", "clave")
    expect_equal(len(signature), 64)
    expect_equal(signature, call("codec", "sign", "mensaje", "clave"))

    expect_equal(call("codec", "equals", "abc", "abc"), True)
    expect_equal(call("codec", "equals", "abc", "abd"), False)
    expect_equal(call("codec", "equals", 1, "1"), True)

    identifier = call("codec", "uuid")
    expect_equal(len(identifier), 36)
    expect(call("codec", "uuid") != identifier)
    expect_equal(call("codec", "uuid5", "koshell"), call("codec", "uuid5", "koshell"))
    expect_equal(len(call("codec", "token", 10)), 10)
    expect_equal(len(call("codec", "password", 12)), 12)
    expect_equal(len(call("codec", "password")), 16)

    expect_raises(Errors.RuntimeError, call, "codec", "base64_decode", "!!!")
    expect_raises(Errors.RuntimeError, call, "codec", "hex_decode", "zz")
    expect_raises(Errors.RuntimeError, call, "codec", "hash", "x", "nope")
    expect_raises(Errors.RuntimeError, call, "codec", "hash", "x", "shake_128")
    expect_raises(Errors.RuntimeError, call, "codec", "hash_file", path("nope.txt"))
    expect_raises(Errors.RuntimeError, call, "codec", "sign", "x", "k", "nope")
    expect_raises(Errors.MismatchType, call, "codec", "hash", None)
    expect_raises(Errors.MismatchType, call, "codec", "token", "x")
    expect_raises(Errors.MismatchType, call, "codec", "password", 1.5)


def test_data():
    json_path = path("data.json")
    payload = {"name": "koshell", "acento": "ñ", "lista": [1, 2, {"a": True}], "n": 3.5}
    expect_equal(call("data", "write_json", json_path, payload), json_path)
    expect_equal(call("data", "read_json", json_path), payload)

    call("filesystem", "write", path("bad.json"), "no es json")
    expect_raises(Errors.RuntimeError, call, "data", "read_json", path("bad.json"))
    expect_raises(Errors.RuntimeError, call, "data", "read_json", path("nope.json"))
    expect_raises(Errors.RuntimeError, call, "data", "write_json", json_path, {1, 2, 3})

    lines_path = path("data.txt")
    expect_equal(call("data", "write_lines", lines_path, ["uno", "dos"]), lines_path)
    call("data", "write_lines", lines_path, ["tres"], True)
    expect_equal(call("data", "read_lines", lines_path), ["uno", "dos", "tres"])
    call("filesystem", "write", path("plain.txt"), "a\nb")
    expect_equal(call("data", "read_lines", path("plain.txt")), ["a", "b"])
    expect_raises(Errors.RuntimeError, call, "data", "read_lines", path("nope.txt"))
    expect_raises(Errors.MismatchType, call, "data", "write_lines", lines_path, "no-array")

    csv_path = path("data.csv")
    rows = [{"mes": "enero", "total": 1200}, {"mes": "febrero", "total": 1450}]
    expect_equal(call("data", "write_csv", csv_path, rows), csv_path)
    call("data", "write_csv", csv_path, [{"mes": "marzo", "total": 980}], True)

    typed = call("data", "read_csv", csv_path, True, True)
    expect_equal(len(typed), 3)
    expect_equal(typed[0]["mes"], "enero")
    expect_equal(typed[1]["total"], 1450)
    expect_native(typed, "data.read_csv")

    raw = call("data", "read_csv", csv_path, False)
    expect_equal(raw[0], ["mes", "total"])
    expect_raises(Errors.RuntimeError, call, "data", "read_csv", path("nope.csv"))

    array_csv = path("array.csv")
    call("data", "write_csv", array_csv, [["a", "b"], ["c", "d"]])
    expect_equal(call("data", "read_csv", array_csv, False), [["a", "b"], ["c", "d"]])
    expect_equal(call("data", "write_csv", path("empty.csv"), []), path("empty.csv"))
    expect_equal(call("data", "read_csv", path("empty.csv")), [])
    expect_raises(Errors.MismatchType, call, "data", "write_csv", csv_path, "no-array")


def test_output():
    buffer = io.StringIO()
    output_module.Output.console = Console(file=buffer, force_terminal=False, width=120)

    try:
        call("output", "info", "marca-info")
        call("output", "success", "marca-ok")
        call("output", "warn", "marca-warn")
        call("output", "error", "marca-error")
        call("output", "debug", "marca-debug")
        call("output", "title", "marca-titulo")
        call("output", "rule", "regla")
        call("output", "panel", "cuerpo-panel", "titulo-panel")
        call("output", "markdown", "**negrita**")
        call("output", "pretty", {"a": [1, 2]})
        call("output", "table", [{"a": 1, "b": 2}, {"a": 3, "b": 4}], ["a", "b"])
        call("output", "table", [["x", "y"]])
        call("output", "table", [])
        call("output", "clear")

        text = buffer.getvalue()
        for marker in ["marca-info", "marca-ok", "marca-warn", "marca-error", "marca-debug",
                       "marca-titulo", "regla", "cuerpo-panel", "negrita", "a"]:
            expect(marker in text, f"output missing {marker}")

        expect_raises(Errors.MismatchType, call, "output", "table", "no-array")
        expect_raises(Errors.MismatchType, call, "output", "table", [{"a": 1}], "no-array")
        expect_raises(Errors.MismatchType, call, "output", "table", [1])
    finally:
        output_module.Output.console = ORIGINAL_CONSOLE


def test_input():
    input_module.Prompt = FakePrompt
    input_module.Confirm = FakePrompt
    input_module.IntPrompt = FakePrompt

    try:
        INPUT_QUEUE[:] = ["aleix"]
        expect_equal(call("input", "ask", "nombre"), "aleix")
        INPUT_QUEUE[:] = [True]
        expect_equal(call("input", "confirm", "seguro"), True)
        INPUT_QUEUE[:] = ["secreto"]
        expect_equal(call("input", "password", "clave"), "secreto")
        INPUT_QUEUE[:] = [7]
        expect_equal(call("input", "number", "puerto"), 7)
        INPUT_QUEUE[:] = ["prod"]
        expect_equal(call("input", "choose", "entorno", ["dev", "prod"]), "prod")

        INPUT_QUEUE[:] = [KeyboardInterrupt()]
        expect_raises(Errors.RuntimeError, call, "input", "ask", "x")
        INPUT_QUEUE[:] = [EOFError()]
        expect_raises(Errors.RuntimeError, call, "input", "confirm", "x")
        INPUT_QUEUE[:] = [KeyboardInterrupt()]
        expect_raises(Errors.RuntimeError, call, "input", "password", "x")
        INPUT_QUEUE[:] = [EOFError()]
        expect_raises(Errors.RuntimeError, call, "input", "number", "x")

        expect_raises(Errors.MismatchType, call, "input", "ask", None)
        expect_raises(Errors.MismatchType, call, "input", "choose", "x", [])
        expect_raises(Errors.MismatchType, call, "input", "choose", "x", "no-array")
    finally:
        input_module.Prompt = ORIGINAL_PROMPT
        input_module.Confirm = ORIGINAL_CONFIRM
        input_module.IntPrompt = ORIGINAL_INTPROMPT


def test_logger():
    log_path = path("app.log")
    expect_equal(call("logger", "levels"), ["debug", "info", "warn", "error"])
    expect_equal(call("logger", "exists", log_path), False)
    expect_equal(call("logger", "read", log_path), [])
    expect_equal(call("logger", "write", log_path, "primera"), log_path)
    call("logger", "write", log_path, "segunda", "warn")
    call("logger", "write", log_path, "tercera", "ERROR")
    expect_equal(call("logger", "exists", log_path), True)
    expect_equal(len(call("logger", "read", log_path)), 3)
    expect_equal(len(call("logger", "read", log_path, 1)), 1)
    expect("tercera" in call("logger", "read", log_path, 1)[0])
    expect_equal(len(call("logger", "read", log_path, 0)), 3)
    expect_equal(call("logger", "tail", log_path, 2), call("logger", "read", log_path, 2))
    expect("WARN segunda" in "\n".join(call("logger", "read", log_path)))
    expect(call("logger", "size", log_path) > 0)
    expect_equal(call("logger", "clear", log_path), log_path)
    expect_equal(call("logger", "size", log_path), 0)
    expect_raises(Errors.RuntimeError, call, "logger", "write", log_path, "x", "nope")
    expect_raises(Errors.RuntimeError, call, "logger", "size", path("nope.log"))
    expect_raises(Errors.MismatchType, call, "logger", "write", log_path, "x", None)
    expect_raises(Errors.MismatchType, call, "logger", "read", log_path, "x")


def test_tasks():
    expect_equal(call("tasks", "clear"), 0)
    expect_equal(call("tasks", "list"), [])

    ticks = []

    def tick():
        ticks.append(time.time())

    job = call("tasks", "every", 0.15, tick, "ticks")
    expect_equal(job, 1)
    time.sleep(0.5)
    expect(len(ticks) >= 2, f"expected ticks, got {len(ticks)}")

    listing = call("tasks", "list")
    expect_equal(len(listing), 1)
    expect_equal(listing[0]["name"], "ticks")
    expect_equal(listing[0]["kind"], "every")
    expect_equal(listing[0]["interval"], 0.15)
    expect_equal(listing[0]["enabled"], True)
    expect(listing[0]["runs"] >= 2)
    expect(listing[0]["last"] is not None)
    expect(0 <= listing[0]["remaining"] <= 0.2)
    expect_native(listing, "tasks.list")

    expect_equal(call("tasks", "pause", job), True)
    before = len(ticks)
    time.sleep(0.4)
    expect_equal(len(ticks), before)
    expect_equal(call("tasks", "list")[0]["enabled"], False)

    expect_equal(call("tasks", "resume", job), True)
    expect_equal(call("tasks", "trigger", job), True)
    expect_equal(len(ticks), before + 1)
    expect(call("tasks", "list")[0]["remaining"] > 0.1)

    once = call("tasks", "after", 0.1, lambda: ticks.append("once"), "una")
    time.sleep(0.5)
    expect("once" in ticks)
    expect(all(item["id"] != once for item in call("tasks", "list")))

    minutes = call("tasks", "every_minutes", 1, "1 + 1", "cada-minuto")
    expect_equal(call("tasks", "list")[1]["interval"], 60.0)
    hours = call("tasks", "every_hours", 1, "1 + 1", "cada-hora")
    expect_equal([item for item in call("tasks", "list") if item["id"] == hours][0]["interval"], 3600.0)

    expect_equal(call("tasks", "cancel", minutes), True)
    expect_equal(call("tasks", "cancel", minutes), False)
    expect_equal(call("tasks", "pause", 999), False)
    expect_equal(call("tasks", "resume", 999), False)
    expect_equal(call("tasks", "trigger", 999), False)
    expect_equal(call("tasks", "clear"), 2)
    expect_equal(call("tasks", "list"), [])

    expect_raises(Errors.RuntimeError, call, "tasks", "every", 0, tick)
    expect_raises(Errors.RuntimeError, call, "tasks", "every", -1, tick)
    expect_raises(Errors.MismatchType, call, "tasks", "every", "x", tick)
    expect_raises(Errors.MismatchType, call, "tasks", "every", 1, None)
    expect_raises(Errors.MismatchType, call, "tasks", "every", 1, 5)
    expect_raises(Errors.MismatchType, call, "tasks", "every", 1, tick, 5)
    expect_raises(Errors.MismatchType, call, "tasks", "cancel", None)
    expect_raises(Errors.MismatchType, call, "tasks", "every_hours", "x", tick)

    failing = call("tasks", "every", 0.1, lambda: (_ for _ in ()).throw(Errors.RuntimeError("boom")))
    time.sleep(0.35)
    expect_equal(len(call("tasks", "list")), 1)
    expect_equal(call("tasks", "clear"), 1)
    expect_equal(failing, 5)


def test_koshell():
    expect_equal(call("koshell", "execute", "1 + 2"), 3)
    expect_equal(call("koshell", "eval", "2 * 3"), 6)

    script = path("script.kos")
    call("filesystem", "write", script, "local x = 10\nx * 4")
    expect_equal(call("koshell", "source", script), 40)
    expect_raises(Errors.RuntimeError, call, "koshell", "source", path("nope.kos"))

    loaded = call("koshell", "loadfrom", BASE + "/script.kos")
    expect_equal(loaded, 42)
    expect_equal(call("koshell", "loadfrom", "http://127.0.0.1:1/nope.kos"), False)

    modules = call("koshell", "modules")
    expect_equal(len(modules), 13)
    expect("filesystem" in modules and "tasks" in modules)
    expect_equal(modules, sorted(modules))

    help_text = call("koshell", "help")
    expect("Koshell" in help_text and "filesystem" in help_text)
    codec_help = call("koshell", "help", "codec")
    expect("codec.hash(" in codec_help and "codec.password(" in codec_help)
    expect_raises(Errors.RuntimeError, call, "koshell", "help", "nope")

    about = call("koshell", "about")
    expect_equal(about["name"], "Koshell")
    expect_equal(about["version"], "2.1.0")
    expect_equal(about["module_count"], 13)
    expect_native(about, "koshell.about")

    buffer = io.StringIO()
    output_module.Output.console = Console(file=buffer, force_terminal=False)
    try:
        call("koshell", "clear")
    finally:
        output_module.Output.console = ORIGINAL_CONSOLE

    expect_raises(SystemExit, call, "koshell", "exit")
    error = expect_raises(SystemExit, call, "koshell", "exit", 3)
    expect_equal(error.code, 3)
    expect_raises(Errors.MismatchType, call, "koshell", "exit", "x")
    expect_raises(Errors.MismatchType, call, "koshell", "loadfrom", "x", "y")
    expect_raises(Errors.RuntimeError, call, "koshell", "source", path("nope.kos"))
    expect_raises(Errors.MismatchType, call, "koshell", "execute", None)


def test_e2e_koskript():
    call("filesystem", "write", path("e2e.txt"), "hola")
    expect_equal(run_script('filesystem.read(filesystem.pathjoin(work, "e2e.txt"))'), "hola")

    seen = []
    result = run_script('''
local files = filesystem.walk(work, (entry) { print("cb:" + entry.name) })
len(files)
''')
    expect(result >= 1)
    expect(any(entry.startswith("cb:") for entry in LOGS))

    echo = run_script('process.run("echo e2e").stdout')
    expect("e2e" in echo)

    expect_equal(run_script('''
env.set("KOSHELL_E2E", "42")
env.get("KOSHELL_E2E")
'''), "42")
    call("env", "unset", "KOSHELL_E2E")

    expect_equal(run_script("system.memory().total > 0"), True)
    expect_equal(run_script("clock.elapsed(clock.now()) >= 0"), True)

    expect_equal(run_script(f'network.get("{BASE}").status'), 200)

    expect_equal(run_script(f'''
local zip = filesystem.pathjoin(work, "e2e.zip")
archive.zip_create(zip, filesystem.pathjoin(work, "e2e.txt"))
archive.contains(zip, "e2e.txt")
'''), True)

    expect_equal(run_script('codec.base64_decode(codec.base64_encode("e2e"))'), "e2e")

    expect_equal(run_script(f'''
local json_path = filesystem.pathjoin(work, "e2e.json")
data.write_json(json_path, {{ "ok": true, "n": 2 }})
data.read_json(json_path).n
'''), 2)

    expect_equal(run_script(f'logger.write(filesystem.pathjoin(work, "e2e.log"), "linea") != null'), True)

    expect_equal(run_script('output.table([{ "a": 1 }])') is None, True)
    expect_equal(run_script('koshell.eval("2 + 2")'), 4)
    expect_equal(run_script('len(koshell.help("clock")) > 0'), True)
    expect_equal(run_script('len(koshell.modules())'), 13)

    INPUT_QUEUE[:] = ["koshell"]
    input_module.Prompt = FakePrompt
    try:
        expect_equal(run_script('input.ask("nombre")'), "koshell")
    finally:
        input_module.Prompt = ORIGINAL_PROMPT

    scheduled = run_script('tasks.every(5, "1 + 1", "e2e-task")')
    expect_equal(len(run_script("tasks.list()")), 1)
    expect_equal(run_script("tasks.clear()"), 1)
    expect(scheduled >= 1)

    expect_raises(Errors.MismatchType, run_script, "codec.hash()")
    expect_raises(Errors.RuntimeError, run_script, 'codec.hash("x", "nope")')
    expect_raises(Errors.RuntimeError, run_script, 'filesystem.read("no-existe-fire.txt")')
    expect_raises(Errors.NameError, run_script, "nombre_que_no_existe")
    expect_raises(Errors.ProtectedObject, run_script, "const FIRE = 1\nFIRE = 2")
    expect_raises(Errors.SyntaxError, run_script, "local = 1")
    expect_raises(Errors.MismatchType, run_script, "len()")


def sweep_targets():
    targets = dict(MODULES)
    targets["koshell"] = KOSHELL
    return targets


def expected_functions():
    names = set()

    for module_name, target in sweep_targets().items():
        for name in public_functions(target):
            names.add(f"{module_name}.{name}")

    return names


def silence_output():
    output_module.Output.console = Console(file=io.StringIO(), force_terminal=False)


def restore_output():
    output_module.Output.console = ORIGINAL_CONSOLE


def sweep_call(label, function, args):
    global CHECKS
    CHECKS += 1
    try:
        value = function(*args)
    except KOSKRIPT_ERRORS:
        return
    except SystemExit:
        return
    except Exception as error:
        raise AssertionError(f"{label} leaked {type(error).__name__}: {error}") from None
    finally:
        if os.getcwd() != SANDBOX:
            os.chdir(SANDBOX)

    expect_native(value, label)


def test_sweep_zero_args():
    silence_output()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        try:
            for module_name, target in sweep_targets().items():
                for name in public_functions(target):
                    function = getattr(target, name)
                    signature = inspect.signature(function)
                    positional = [
                        parameter for parameter in signature.parameters.values()
                        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
                    ]
                    minimum = sum(1 for parameter in positional if parameter.default is parameter.empty)
                    if minimum == 0:
                        sweep_call(f"{module_name}.{name}()", function, [])
        finally:
            restore_output()


def test_sweep_wrong_arity():
    for module_name, target in sweep_targets().items():
        for name in public_functions(target):
            function = getattr(target, name)
            signature = inspect.signature(function)
            if any(parameter.kind == parameter.VAR_POSITIONAL for parameter in signature.parameters.values()):
                continue
            sweep_call(f"{module_name}.{name}(x99)", function, [None] * 99)


def test_sweep_null_args():
    silence_output()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        try:
            for module_name, target in sweep_targets().items():
                for name in public_functions(target):
                    function = getattr(target, name)
                    signature = inspect.signature(function)
                    positional = [
                        parameter for parameter in signature.parameters.values()
                        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
                    ]
                    minimum = sum(1 for parameter in positional if parameter.default is parameter.empty)
                    if minimum > 0:
                        sweep_call(f"{module_name}.{name}(null)", function, [None] * minimum)
        finally:
            restore_output()


def test_sweep_wrong_types():
    silence_output()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        try:
            for module_name, target in sweep_targets().items():
                if module_name == "input":
                    continue
                for name in public_functions(target):
                    function = getattr(target, name)
                    signature = inspect.signature(function)
                    positional = [
                        parameter for parameter in signature.parameters.values()
                        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
                    ]
                    minimum = sum(1 for parameter in positional if parameter.default is parameter.empty)
                    if minimum > 0:
                        sweep_call(f"{module_name}.{name}(\"x\")", function, ["x"] * minimum)
        finally:
            restore_output()
            os.environ.clear()
            os.environ.update(ENV_SNAPSHOT)


def test_thread_safety():
    ticks = []

    def tick():
        ticks.append(time.time())

    call("tasks", "every", 0.05, tick)
    for _ in range(60):
        expect_equal(run_script("1 + 1"), 2)
    time.sleep(0.4)
    expect(len(ticks) >= 1, f"task did not run between commands: {len(ticks)}")
    expect_equal(call("tasks", "clear"), 1)
    expect_equal(THREAD_ERRORS, [])


def test_coverage():
    uncovered = sorted(expected_functions() - COVERED)
    expect_equal(uncovered, [], "uncovered functions")


def test_no_thread_errors():
    expect_equal(THREAD_ERRORS, [])


def run_test(function):
    global PASSED
    try:
        function()
    except Exception as error:
        FAILURES.append(f"{function.__name__}: {error}")
        print(f"FAIL  {function.__name__}: {error}")
        traceback.print_exc()
        return
    PASSED += 1
    print(f"PASS  {function.__name__}")


def cleanup():
    for child in list(CHILDREN):
        try:
            call("process", "kill_task", child)
        except Exception:
            pass
    try:
        call("tasks", "clear")
    except Exception:
        pass
    os.chdir(WORK)
    os.environ.clear()
    os.environ.update(ENV_SNAPSHOT)
    output_module.Output.console = ORIGINAL_CONSOLE
    input_module.Prompt = ORIGINAL_PROMPT
    input_module.Confirm = ORIGINAL_CONFIRM
    input_module.IntPrompt = ORIGINAL_INTPROMPT
    threading.excepthook = ORIGINAL_THREAD_HOOK
    server.shutdown()
    server.server_close()
    shutil.rmtree(WORK, ignore_errors=True)


def main():
    threading.excepthook = thread_hook
    os.chdir(SANDBOX)

    tests = [
        test_harness,
        test_filesystem_paths,
        test_filesystem_queries,
        test_filesystem_directories,
        test_filesystem_files,
        test_filesystem_search,
        test_process,
        test_env,
        test_system,
        test_clock,
        test_network,
        test_archive,
        test_codec,
        test_data,
        test_output,
        test_input,
        test_logger,
        test_tasks,
        test_koshell,
        test_e2e_koskript,
        test_sweep_zero_args,
        test_sweep_wrong_arity,
        test_sweep_null_args,
        test_sweep_wrong_types,
        test_thread_safety,
        test_coverage,
        test_no_thread_errors,
    ]

    print("=" * 60)
    print("FIRE TEST — Koshell standard library")
    print("=" * 60)

    try:
        for test in tests:
            run_test(test)
    finally:
        cleanup()

    print("-" * 60)
    print(f"Tests:    {PASSED} passed, {len(FAILURES)} failed")
    print(f"Checks:   {CHECKS}")
    print(f"Coverage: {len(COVERED)}/{len(expected_functions())} functions exercised")
    print(f"Threads:  {'errors: ' + '; '.join(THREAD_ERRORS) if THREAD_ERRORS else 'no unhandled errors'}")

    if FAILURES:
        print("Failures:")
        for failure in FAILURES:
            print(f"  - {failure}")
        print("RESULT: FAIL")
        return 1

    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
