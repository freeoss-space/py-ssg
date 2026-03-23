import os
from pathlib import Path

import mistune


class MarkdownParser:
    def __init__(self, content_dir: Path):
        self.content_dir = content_dir

    def parse(self) -> dict[str, str]:
        result = {}
        for filename in os.listdir(self.content_dir):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(self.content_dir, filename)
            with open(filepath) as f:
                content = f.read()
            result[filename] = mistune.html(content)
        return result
