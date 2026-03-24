import os
from pathlib import Path

from pyssg.commands.base_command import BaseCommand
from pyssg.modules.html import HtmlTemplateEngine
from pyssg.modules.markdown import MarkdownParser


class BuildCommand(BaseCommand):
    def execute(self) -> None:
        project_dir = Path.cwd()
        templates_dir = project_dir / "templates"
        components_dir = project_dir / "components"
        output_dir = project_dir / "output"

        self._info("Parsing markdown files...")
        parser = MarkdownParser(content_dir=project_dir / "content")
        collection = parser.parse()

        self._info("Rendering templates...")
        component_names = [
            f.removesuffix(".html")
            for f in os.listdir(components_dir)
            if f.endswith(".html")
        ]
        engine = HtmlTemplateEngine(
            templates_dir=templates_dir,
            components_dir=components_dir,
            component_names=component_names,
        )
        os.makedirs(output_dir, exist_ok=True)

        for filename in os.listdir(templates_dir):
            if not filename.endswith(".html"):
                continue
            filepath = os.path.join(templates_dir, filename)
            with open(filepath) as f:
                template = f.read()

            rendered = engine.render(template, context={"content": list(collection)})

            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w") as f:
                f.write(rendered)

        self._success("Build complete!")
