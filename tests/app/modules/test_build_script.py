from pathlib import Path
from unittest.mock import MagicMock, patch

from pyssg.modules.build_script import BuildContext, BuildScript
from pyssg.modules.cache import BuildCache
from pyssg.modules.config import SiteConfig
from pyssg.modules.markdown import MarkdownCollection

TEST_PATH = "pyssg.modules.build_script"


def _make_context(**overrides):
    return BuildContext(
        config=overrides.get("config", SiteConfig()),
        cache=overrides.get("cache", MagicMock(spec=BuildCache)),
        project_dir=overrides.get("project_dir", Path("/project")),
        templates_dir=overrides.get("templates_dir", Path("/project/templates")),
        components_dir=overrides.get("components_dir", Path("/project/components")),
        output_dir=overrides.get("output_dir", Path("/project/output")),
        content=overrides.get("content", None),
    )


class TestBuildContext:
    def test_default_content_is_none(self):
        ctx = _make_context()

        assert ctx.content is None

    def test_stores_config(self):
        config = SiteConfig(name="My Site")
        ctx = _make_context(config=config)

        assert ctx.config.name == "My Site"

    def test_stores_paths(self):
        ctx = _make_context(
            project_dir=Path("/a"),
            templates_dir=Path("/b"),
            components_dir=Path("/c"),
            output_dir=Path("/d"),
        )

        assert ctx.project_dir == Path("/a")
        assert ctx.templates_dir == Path("/b")
        assert ctx.components_dir == Path("/c")
        assert ctx.output_dir == Path("/d")

    def test_stores_content(self):
        collection = MarkdownCollection()
        ctx = _make_context(content=collection)

        assert ctx.content is collection


class TestBuildScriptLoad:
    @patch(f"{TEST_PATH}.Path")
    def test_no_script_file(self, mock_path):
        mock_path.return_value.__truediv__ = lambda self, x: MagicMock(
            exists=lambda: False
        )

        script = BuildScript(Path("/project"))

        assert not script.has_script

    def test_loads_script_with_hooks(self, tmp_path):
        script_file = tmp_path / "pyssg_build.py"
        script_file.write_text(
            "def before_build(context):\n    context.config.name = 'hooked'\n"
        )

        script = BuildScript(tmp_path)

        assert script.has_script


class TestBuildScriptHooks:
    def test_before_build_calls_hook(self, tmp_path):
        script_file = tmp_path / "pyssg_build.py"
        script_file.write_text(
            "def before_build(context):\n    context.config.name = 'hooked'\n"
        )
        script = BuildScript(tmp_path)
        ctx = _make_context(config=SiteConfig(name="original"))

        script.before_build(ctx)

        assert ctx.config.name == "hooked"

    def test_before_markdown_parsing_calls_hook(self, tmp_path):
        script_file = tmp_path / "pyssg_build.py"
        script_file.write_text(
            "def before_markdown_parsing(context):\n"
            "    context.config.description = 'parsed'\n"
        )
        script = BuildScript(tmp_path)
        ctx = _make_context()

        script.before_markdown_parsing(ctx)

        assert ctx.config.description == "parsed"

    def test_before_component_parsing_calls_hook(self, tmp_path):
        script_file = tmp_path / "pyssg_build.py"
        script_file.write_text(
            "def before_component_parsing(context):\n"
            "    context.config.url = 'https://modified.com'\n"
        )
        script = BuildScript(tmp_path)
        ctx = _make_context()

        script.before_component_parsing(ctx)

        assert ctx.config.url == "https://modified.com"

    def test_after_build_calls_hook(self, tmp_path):
        script_file = tmp_path / "pyssg_build.py"
        script_file.write_text(
            "def after_build(context):\n    context.config.name = 'done'\n"
        )
        script = BuildScript(tmp_path)
        ctx = _make_context()

        script.after_build(ctx)

        assert ctx.config.name == "done"

    def test_missing_hook_is_noop(self, tmp_path):
        script_file = tmp_path / "pyssg_build.py"
        script_file.write_text("# no hooks defined\n")
        script = BuildScript(tmp_path)
        ctx = _make_context(config=SiteConfig(name="unchanged"))

        script.before_build(ctx)

        assert ctx.config.name == "unchanged"

    def test_no_script_hooks_are_noop(self):
        script = BuildScript(Path("/nonexistent"))
        ctx = _make_context(config=SiteConfig(name="unchanged"))

        script.before_build(ctx)
        script.before_markdown_parsing(ctx)
        script.before_component_parsing(ctx)
        script.after_build(ctx)

        assert ctx.config.name == "unchanged"

    def test_hook_receives_content(self, tmp_path):
        script_file = tmp_path / "pyssg_build.py"
        script_file.write_text(
            "def after_build(context):\n"
            "    context.config.name = str(len(context.content))\n"
        )
        script = BuildScript(tmp_path)
        collection = MarkdownCollection()
        ctx = _make_context(content=collection)

        script.after_build(ctx)

        assert ctx.config.name == "0"
