from unittest.mock import call, patch

import pytest

from pyssg.commands.base_command import BaseCommand

TEST_PATH = "pyssg.commands.base_command"

TERM_LENGTH = 40
PREFIX = "[bold blue][INFO][/bold blue] "
TEXT_WIDTH = TERM_LENGTH - len("INFO") - 4


class ConcreteCommand(BaseCommand):
    def execute(self) -> None:
        pass


class TestPrintBlock:
    @patch(f"{TEST_PATH}.rich_print")
    @patch(f"{TEST_PATH}.shutil")
    def test_prints_status_line(self, mock_shutil, mock_rich_print):
        mock_shutil.get_terminal_size.return_value.columns = TERM_LENGTH
        command = ConcreteCommand()

        command._print_block("hello", color="blue")

        assert mock_rich_print.call_args_list == [
            call(f"{PREFIX}hello"),
        ]

    @patch(f"{TEST_PATH}.rich_print")
    @patch(f"{TEST_PATH}.shutil")
    def test_wraps_long_message(self, mock_shutil, mock_rich_print):
        mock_shutil.get_terminal_size.return_value.columns = TERM_LENGTH
        command = ConcreteCommand()
        long_message = "a " * (TEXT_WIDTH + 1)

        command._print_block(long_message.strip(), color="blue")

        assert mock_rich_print.call_count >= 2
        assert mock_rich_print.call_args_list[0].args[0].startswith(PREFIX)
        for wrapped_line in mock_rich_print.call_args_list[1:]:
            assert wrapped_line.args[0].startswith(" " * len(PREFIX))

    @patch(f"{TEST_PATH}.rich_print")
    @patch(f"{TEST_PATH}.shutil")
    def test_empty_message_prints_label_only(self, mock_shutil, mock_rich_print):
        mock_shutil.get_terminal_size.return_value.columns = TERM_LENGTH
        command = ConcreteCommand()

        command._print_block("", color="blue")

        assert mock_rich_print.call_args_list == [call(PREFIX.rstrip())]


class TestInfo:
    @patch.object(ConcreteCommand, "_print_block")
    def test_uses_blue(self, mock_print_block):
        ConcreteCommand()._info("hello")
        mock_print_block.assert_called_once_with("hello", color="blue")


class TestDetail:
    @patch.object(ConcreteCommand, "_info")
    def test_skips_info_when_verbose_disabled(self, mock_info):
        ConcreteCommand()._detail("hello")
        mock_info.assert_not_called()

    @patch.object(ConcreteCommand, "_info")
    def test_uses_info_when_verbose_enabled(self, mock_info):
        ConcreteCommand(verbose=True)._detail("hello")
        mock_info.assert_called_once_with("hello")


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
