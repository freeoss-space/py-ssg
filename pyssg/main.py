import logging

import typer

from pyssg.commands.build import BuildCommand
from pyssg.commands.init import InitCommand
from pyssg.commands.serve import ServeCommand

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


@app.command()
def serve(port: int | None = typer.Option(default=None)) -> None:
    serve_command = ServeCommand(port=port)
    serve_command.execute()


if __name__ == "__main__":
    main()
