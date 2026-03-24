import mistune
from pygments import highlight
from pygments.formatters import HtmlFormatter  # type: ignore[attr-defined]
from pygments.lexers import TextLexer, get_lexer_by_name  # type: ignore[attr-defined]


class _HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code: str, info: str | None = None) -> str:
        if info:
            try:
                lexer = get_lexer_by_name(info, stripall=True)
            except Exception:
                lexer = TextLexer()
        else:
            lexer = TextLexer()
        formatter = HtmlFormatter(cssclass="highlight")
        return highlight(code, lexer, formatter)


class SyntaxHighlighter:
    def __init__(
        self,
        theme_light: str = "friendly",
        theme_dark: str = "monokai",
    ):
        self.theme_light = theme_light
        self.theme_dark = theme_dark
        self._markdown = mistune.create_markdown(renderer=_HighlightRenderer())

    def render_markdown(self, text: str) -> str:
        return str(self._markdown(text))

    def get_stylesheet(self) -> str:
        light_css = HtmlFormatter(style=self.theme_light).get_style_defs(".highlight")
        dark_css = HtmlFormatter(style=self.theme_dark).get_style_defs(".highlight")
        return (
            f"@media (prefers-color-scheme: light) {{\n{light_css}\n}}\n"
            f"@media (prefers-color-scheme: dark) {{\n{dark_css}\n}}"
        )
