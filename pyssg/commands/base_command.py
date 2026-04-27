import shutil
import textwrap

from rich import print as rich_print


class BaseCommand:
    _verbose: bool = False
    _dry_run: bool = False

    def __init__(self, *, verbose: bool = False, dry_run: bool = False) -> None:
        self._verbose = verbose
        self._dry_run = dry_run

    def _status_prefix(self, color: str) -> str:
        labels = {
            "blue": "INFO",
            "green": "DONE",
            "yellow": "WARN",
            "red": "FAIL",
        }
        label = labels.get(color, "LOG")
        return f"[bold {color}][{label}][/bold {color}]"

    def _print_block(self, message: str, color: str) -> None:
        prefix = self._status_prefix(color)
        available_width = max(shutil.get_terminal_size().columns - 8, 20)
        message_width = max(available_width - len("INFO"), 12)
        wrapped_lines = textwrap.wrap(message, width=message_width) or [""]

        for index, line in enumerate(wrapped_lines):
            if index == 0:
                if line:
                    rich_print(f"{prefix} {line}")
                else:
                    rich_print(prefix)
                continue
            rich_print(f"{' ' * (len(prefix) + 1)}{line}")

    def _info(self, message: str) -> None:
        self._print_block(message, color="blue")

    def _detail(self, message: str) -> None:
        if not self._verbose:
            return
        self._info(message)

    def _success(self, message: str) -> None:
        self._print_block(message, color="green")

    def _warning(self, message: str) -> None:
        self._print_block(message, color="yellow")

    def _error(self, message: str) -> None:
        self._print_block(message, color="red")

    def execute(self) -> None:
        raise NotImplementedError
