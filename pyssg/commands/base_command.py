import shutil
import textwrap

from rich import print as rich_print


class BaseCommand:
    def _print_block(self, message: str, color: str) -> None:
        term_length = shutil.get_terminal_size().columns
        content_width = term_length - 1
        text_width = content_width - 4  # 2-char padding on each side

        padding_line = f"[bold {color}]┃[/bold {color}]{' ' * content_width}"
        rich_print(padding_line)
        for chunk in textwrap.wrap(message, width=text_width) or [""]:
            padded = f"  {chunk:<{text_width}}  "
            rich_print(f"[bold {color}]┃{padded}[/bold {color}]")
        rich_print(padding_line)

    def _info(self, message: str) -> None:
        self._print_block(message, color="blue")

    def _success(self, message: str) -> None:
        self._print_block(message, color="green")

    def _warning(self, message: str) -> None:
        self._print_block(message, color="yellow")

    def _error(self, message: str) -> None:
        self._print_block(message, color="red")

    def execute(self) -> None:
        raise NotImplementedError
