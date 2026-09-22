from . import arity, bridge
from .archive import Archive
from .clock import Clock
from .codec import Codec
from .data import Data
from .environment import Environment
from .filesystem import Filesystem
from .input import Input
from .koshell import Koshell
from .logger import Logger
from .network import Network
from .output import Output
from .processes import Process
from .system import System
from .tasks import Tasks

VERSION = "2.1.0"

MODULES = {
    "filesystem": Filesystem,
    "process": Process,
    "env": Environment,
    "system": System,
    "clock": Clock,
    "network": Network,
    "archive": Archive,
    "codec": Codec,
    "data": Data,
    "output": Output,
    "input": Input,
    "logger": Logger,
    "tasks": Tasks,
}


def execution_lock():
    return bridge.lock()


def register_standard(runtime, extra=None):
    modules = dict(MODULES)

    if extra:
        modules.update(extra)

    wrapped = {name: arity.wrap(name, target) for name, target in modules.items()}

    bridge.use(runtime)
    runtime.register_many(wrapped)
    runtime.register("koshell", arity.wrap("koshell", Koshell)(runtime, wrapped, VERSION))
    return runtime
