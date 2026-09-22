from koskript import KoskriptRuntime
from rich.console import Console
from rich.text import Text
from standard import execution_lock, register_standard
import getpass, os, socket

runtime = KoskriptRuntime()
console = Console()
runtime.register("print", console.print)
register_standard(runtime)


def main():
    while True:
        try:
            incmd = console.input(
                f"[red]{getpass.getuser()}[/red][bold]@[/bold][magenta]{socket.gethostname()}[/magenta] "
                f"[blue bold]{os.getcwd()}[/blue bold] $ ")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not incmd.strip():
            continue

        try:
            with execution_lock():
                result = runtime.execute(incmd)
        except Exception as error:
            console.print(Text.assemble((type(error).__name__, "bold red"), ": ", str(error)))
            continue

        if result is None:
            continue

        console.print(result)


if __name__ == "__main__":
    main()
