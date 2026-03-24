from pyssg.modules.syntax import SyntaxHighlighter


class TestRenderMarkdown:
    def test_highlights_python_code_block(self):
        highlighter = SyntaxHighlighter()
        md = '```python\nprint("hello")\n```'

        result = highlighter.render_markdown(md)

        assert "highlight" in result
        assert "print" in result

    def test_renders_plain_markdown_without_code(self):
        highlighter = SyntaxHighlighter()
        md = "# Hello\n\nWorld"

        result = highlighter.render_markdown(md)

        assert "<h1>Hello</h1>" in result
        assert "<p>World</p>" in result

    def test_code_block_without_language_falls_back_to_text(self):
        highlighter = SyntaxHighlighter()
        md = "```\nplain text\n```"

        result = highlighter.render_markdown(md)

        assert "plain text" in result

    def test_uses_css_classes_not_inline_styles(self):
        highlighter = SyntaxHighlighter()
        md = "```python\ndef foo(): pass\n```"

        result = highlighter.render_markdown(md)

        assert 'style="' not in result

    def test_unknown_language_falls_back_to_text(self):
        highlighter = SyntaxHighlighter()
        md = "```notareallanguage\nsome code\n```"

        result = highlighter.render_markdown(md)

        assert "some code" in result


class TestGetStylesheet:
    def test_returns_css_with_light_and_dark_media_queries(self):
        highlighter = SyntaxHighlighter(theme_light="friendly", theme_dark="monokai")

        css = highlighter.get_stylesheet()

        assert "prefers-color-scheme: light" in css
        assert "prefers-color-scheme: dark" in css
        assert ".highlight" in css

    def test_returns_different_css_for_different_themes(self):
        css1 = SyntaxHighlighter(
            theme_light="friendly", theme_dark="monokai"
        ).get_stylesheet()
        css2 = SyntaxHighlighter(
            theme_light="tango", theme_dark="dracula"
        ).get_stylesheet()

        assert css1 != css2
