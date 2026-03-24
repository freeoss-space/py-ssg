import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from pyssg.modules.cache import BuildCache
from pyssg.modules.config import SiteConfig
from pyssg.modules.markdown import MarkdownCollection

SCRIPT_FILENAME = "pyssg_build.py"


@dataclass
class BuildContext:
    config: SiteConfig
    cache: BuildCache
    project_dir: Path
    templates_dir: Path
    components_dir: Path
    output_dir: Path
    content: MarkdownCollection | None = field(default=None)


class BuildScript:
    def __init__(self, project_dir: Path):
        self._module: ModuleType | None = None
        script_path = project_dir / SCRIPT_FILENAME
        if script_path.exists():
            spec = importlib.util.spec_from_file_location("pyssg_build", script_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._module = module

    @property
    def has_script(self) -> bool:
        return self._module is not None

    def _call_hook(self, name: str, context: BuildContext) -> None:
        if self._module is None:
            return
        hook = getattr(self._module, name, None)
        if hook and callable(hook):
            hook(context)

    def before_build(self, context: BuildContext) -> None:
        self._call_hook("before_build", context)

    def before_markdown_parsing(self, context: BuildContext) -> None:
        self._call_hook("before_markdown_parsing", context)

    def before_component_parsing(self, context: BuildContext) -> None:
        self._call_hook("before_component_parsing", context)

    def after_build(self, context: BuildContext) -> None:
        self._call_hook("after_build", context)
