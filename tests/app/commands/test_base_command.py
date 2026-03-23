from unittest.mock import call, patch

import pytest

from pyssg.modules.commands.base_command import BaseCommand

TEST_PATH = "pyssg.modules.commands.base_command"

TERM_LENGTH = 40
CONTENT_WIDTH = TERM_LENGTH - 1
TEXT_WIDTH = CONTENT_WIDTH - 4  # 2-char padding on each side


class ConcreteCommand(BaseCommand):
    def execute(self) -> None:
        pass


class TestPrintBlock:
    @patch(f"{TEST_PATH}.rich_print")
    @patch(f"{TEST_PATH}.shutil")
    def test_prints_border_and_message(self, mock_shutil, mock_rich_print):
        mock_shutil.get_terminal_size.return_value.columns = TERM_LENGTH
        command = ConcreteCommand()

        command._print_block("hello", color="blue")

        spaces = " " * CONTENT_WIDTH
        padding_line = f"[bold blue]┃[/bold blue]{spaces}"
        padded = f"  {'hello':<{TEXT_WIDTH}}  "
        message_line = f"[bold blue]┃{padded}[/bold blue]"
        assert mock_rich_print.call_args_list == [
            call(padding_line),
            call(message_line),
            call(padding_line),
        ]

    @patch(f"{TEST_PATH}.rich_print")
    @patch(f"{TEST_PATH}.shutil")
    def test_wraps_long_message(self, mock_shutil, mock_rich_print):
        mock_shutil.get_terminal_size.return_value.columns = TERM_LENGTH
        command = ConcreteCommand()
        long_message = "a " * (TEXT_WIDTH + 1)

        command._print_block(long_message.strip(), color="blue")

        # padding + at least 2 message lines + padding
        assert mock_rich_print.call_count >= 4

    @patch(f"{TEST_PATH}.rich_print")
    @patch(f"{TEST_PATH}.shutil")
    def test_empty_message_prints_blank_line(self, mock_shutil, mock_rich_print):
        mock_shutil.get_terminal_size.return_value.columns = TERM_LENGTH
        command = ConcreteCommand()

        command._print_block("", color="blue")

        padded = f"  {'':<{TEXT_WIDTH}}  "
        message_line = f"[bold blue]┃{padded}[/bold blue]"
        assert mock_rich_print.call_args_list[1] == call(message_line)


class TestInfo:
    @patch.object(ConcreteCommand, "_print_block")
    def test_uses_blue(self, mock_print_block):
        ConcreteCommand()._info("hello")
        mock_print_block.assert_called_once_with("hello", color="blue")


class TestSuccess:
    @patch.object(ConcreteCommand, "_print_block")
    def test_uses_green(self, mock_print_block):
        ConcreteCommand()._success("hello")
        mock_print_block.assert_called_once_with("hello", color="green")


class TestWarning:
    @patch.object(ConcreteCommand, "_print_block")
    def test_uses_yellow(self, mock_print_block):
        ConcreteCommand()._warning("hello")
        mock_print_block.assert_called_once_with("hello", color="yellow")


class TestError:
    @patch.object(ConcreteCommand, "_print_block")
    def test_uses_red(self, mock_print_block):
        ConcreteCommand()._error("hello")
        mock_print_block.assert_called_once_with("hello", color="red")


class TestExecute:
    def test_raises_not_implemented(self):
        class Incomplete(BaseCommand):
            pass

        with pytest.raises(NotImplementedError):
            Incomplete().execute()
