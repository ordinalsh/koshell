from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from .helpers import expect_array


def _label(name, color, message):
    line = Text.from_markup(f"[bold {color}]{name}[/bold {color}] ")
    line.append(str(message))
    return line


class Output:
    console = Console()

    def info(message):
        Output.console.print(_label("info", "blue", message))

    def success(message):
        Output.console.print(_label("ok", "green", message))

    def warn(message):
        Output.console.print(_label("warn", "yellow", message))

    def error(message):
        Output.console.print(_label("error", "red", message))

    def debug(message):
        Output.console.print(_label("debug", "dim", message))

    def title(message):
        Output.console.print(Text(str(message), style="bold"))

    def rule(label=""):
        Output.console.rule(str(label))

    def panel(message, title=None):
        Output.console.print(Panel(str(message), title=title))

    def markdown(text):
        Output.console.print(Markdown(str(text)))

    def pretty(value):
        Output.console.print(Pretty(value))

    def clear():
        Output.console.clear()

    def table(rows, columns=None):
        expect_array("output.table", rows)
        table = Table(show_header=True, header_style="bold")

        if columns is not None:
            expect_array("output.table", columns)
            for column in columns:
                table.add_column(str(column))

            for row in rows:
                if isinstance(row, dict):
                    table.add_row(*[str(row.get(str(column), "")) for column in columns])
                else:
                    table.add_row(*[str(value) for value in expect_array("output.table", row)])
        elif rows and isinstance(rows[0], dict):
            keys = list(rows[0].keys())

            for key in keys:
                table.add_column(str(key))

            for row in rows:
                table.add_row(*[str(row.get(key, "")) for key in keys])
        else:
            if rows:
                for index in range(len(expect_array("output.table", rows[0]))):
                    table.add_column(str(index + 1))

            for row in rows:
                table.add_row(*[str(value) for value in expect_array("output.table", row)])

        Output.console.print(table)
        return None
