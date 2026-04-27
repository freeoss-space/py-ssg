import logging

import typer

from pyssg.commands.build import BuildCommand
from pyssg.commands.init import InitCommand
from pyssg.commands.new import NewCommand
from pyssg.commands.serve import ServeCommand

LOGGER = logging.getLogger(__name__)
app = typer.Typer()


def main():
    app()


@app.callback()
def callback() -> None:
    pass


@app.command()
def init(
    folder_name: str = typer.Argument(default="."),
    verbose: bool = typer.Option(default=False, help="Show additional details."),
    dry_run: bool = typer.Option(
        default=False, help="Preview changes without writing files."
    ),
) -> None:
    init_command = InitCommand(
        folder_name=folder_name,
        verbose=verbose,
        dry_run=dry_run,
    )
    init_command.execute()


@app.command()
def build(
    verbose: bool = typer.Option(default=False, help="Show additional details."),
    dry_run: bool = typer.Option(
        default=False, help="Preview changes without writing files."
    ),
) -> None:
    build_command = BuildCommand(verbose=verbose, dry_run=dry_run)
    build_command.execute()


@app.command()
def serve(
    port: int | None = typer.Option(default=None),
    verbose: bool = typer.Option(default=False, help="Show additional details."),
    dry_run: bool = typer.Option(
        default=False, help="Preview startup without writing files or serving."
    ),
) -> None:
    serve_command = ServeCommand(port=port, verbose=verbose, dry_run=dry_run)
    serve_command.execute()


@app.command()
def new(
    title: str = typer.Argument(),
    sub_folder: str | None = typer.Option(default=None, help="Optional content sub-folder."),
    verbose: bool = typer.Option(default=False, help="Show additional details."),
    dry_run: bool = typer.Option(
        default=False, help="Preview changes without writing files."
    ),
) -> None:
    new_command = NewCommand(
        title=title,
        sub_folder=sub_folder,
        verbose=verbose,
        dry_run=dry_run,
    )
    new_command.execute()


if __name__ == "__main__":
    main()
