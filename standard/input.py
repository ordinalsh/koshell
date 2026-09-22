from rich.prompt import Confirm, IntPrompt, Prompt

from koskript import Errors

from .helpers import expect_array, expect_string


class Input:
    def ask(prompt, default=None):
        expect_string("input.ask", prompt)

        try:
            return Prompt.ask(prompt, default=default)
        except (EOFError, KeyboardInterrupt):
            raise Errors.RuntimeError("input.ask() was cancelled") from None

    def confirm(prompt, default=False):
        expect_string("input.confirm", prompt)

        try:
            return Confirm.ask(prompt, default=default)
        except (EOFError, KeyboardInterrupt):
            raise Errors.RuntimeError("input.confirm() was cancelled") from None

    def password(prompt):
        expect_string("input.password", prompt)

        try:
            return Prompt.ask(prompt, password=True)
        except (EOFError, KeyboardInterrupt):
            raise Errors.RuntimeError("input.password() was cancelled") from None

    def number(prompt, default=None):
        expect_string("input.number", prompt)

        try:
            return IntPrompt.ask(prompt, default=default)
        except (EOFError, KeyboardInterrupt):
            raise Errors.RuntimeError("input.number() was cancelled") from None

    def choose(prompt, options):
        expect_string("input.choose", prompt)
        expect_array("input.choose", options)

        if not options:
            raise Errors.MismatchType("input.choose() expected a non-empty array")

        choices = [str(option) for option in options]

        try:
            selected = Prompt.ask(prompt, choices=choices, default=choices[0])
        except (EOFError, KeyboardInterrupt):
            raise Errors.RuntimeError("input.choose() was cancelled") from None

        return options[choices.index(selected)]
