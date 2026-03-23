import logging

import typer

from pyssg.modules.commands.init import InitCommand

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


if __name__ == "__main__":
    main()
