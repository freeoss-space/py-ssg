import logging

import typer

from pyssg.commands.build import BuildCommand
from pyssg.commands.init import InitCommand

LOGGER = logging.getLogger(__name__)
app = typer.Typer()


def main():
    app()


@app.callback()
def callback() -> None:
    pass


@app.command()
def init(folder_name: str = typer.Argument(default=".")) -> None:
    init_command = InitCommand(folder_name=folder_name)
    init_command.execute()


@app.command()
def build() -> None:
    build_command = BuildCommand()
    build_command.execute()


if __name__ == "__main__":
    main()
