from pathlib import Path
from unittest.mock import mock_open, patch

from pyssg.modules.config import AuthorConfig, SiteConfig
from pyssg.modules.html import HtmlTemplateEngine
from pyssg.modules.markdown import MarkdownContent

TEST_PATH = "pyssg.modules.html"


class TestRenderComponent:
    def test_replaces_component_tag_with_file_content(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Navbar"],
        )
        template = "<Navbar />"
        navbar_html = "<nav>Home</nav>"

        with patch(f"{TEST_PATH}.open", mock_open(read_data=navbar_html)):
            result = engine.render(template)

        assert "<nav>Home</nav>" in result

    def test_passes_attributes_as_jinja2_variables(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Navbar"],
        )
        template = '<Navbar homeClass="active" />'
        navbar_html = '<nav><a href="/" class="{{ homeClass }}">Home</a></nav>'

        with patch(f"{TEST_PATH}.open", mock_open(read_data=navbar_html)):
            result = engine.render(template)

        assert 'class="active"' in result

    def test_jinja2_condition_true(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Navbar"],
        )
        template = '<Navbar activeUrl="home" />'
        navbar_html = (
            '<a class="{% if activeUrl == "home" %}active{% endif %}">Home</a>'
        )

        with patch(f"{TEST_PATH}.open", mock_open(read_data=navbar_html)):
            result = engine.render(template)

        assert 'class="active"' in result

    def test_jinja2_condition_false(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Navbar"],
        )
        template = '<Navbar activeUrl="about" />'
        navbar_html = (
            '<a class="{% if activeUrl == "home" %}active{% endif %}">Home</a>'
        )

        with patch(f"{TEST_PATH}.open", mock_open(read_data=navbar_html)):
            result = engine.render(template)

        assert 'class=""' in result

    def test_multiple_components(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Header", "Footer"],
        )
        template = "<Header />\n<main>Content</main>\n<Footer />"

        def side_effect(path, *args, **kwargs):
            content = {
                "/components/Header.html": "<header>Header</header>",
                "/components/Footer.html": "<footer>Footer</footer>",
            }
            return mock_open(read_data=content[str(path)])()

        with patch(f"{TEST_PATH}.open", side_effect=side_effect):
            result = engine.render(template)

        assert "<header>Header</header>" in result
        assert "<footer>Footer</footer>" in result
        assert "<main>Content</main>" in result

    def test_ignores_unknown_tags(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Navbar"],
        )
        template = '<div><Unknown prop="val" /></div>'

        result = engine.render(template)

        assert "Unknown" in result

    def test_component_with_no_attributes(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Navbar"],
        )
        template = "<Navbar />"
        navbar_html = "<nav>Static content</nav>"

        with patch(f"{TEST_PATH}.open", mock_open(read_data=navbar_html)):
            result = engine.render(template)

        assert "<nav>Static content</nav>" in result


class TestRenderTemplate:
    def _make_engine(self, config=None):
        return HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=[],
            config=config,
        )

    def test_renders_jinja2_variable(self):
        engine = self._make_engine()
        template = "<h1>{{ title }}</h1>"

        result = engine.render(template, context={"title": "Hello"})

        assert "<h1>Hello</h1>" in result

    def test_renders_jinja2_for_loop(self):
        engine = self._make_engine()
        template = "{% for post in posts %}<p>{{ post.title }}</p>{% endfor %}"

        posts = [
            MarkdownContent(filename="", html="<p>a</p>", title="First"),
            MarkdownContent(filename="", html="<p>b</p>", title="Second"),
        ]

        result = engine.render(template, context={"posts": posts})

        assert "<p>First</p>" in result
        assert "<p>Second</p>" in result

    def test_renders_jinja2_for_loop_with_nested_fields(self):
        engine = self._make_engine()
        template = "{% for post in posts %}<h2>{{ post.title }}</h2>{{ post.html }}{% endfor %}"

        posts = [
            MarkdownContent(filename="", html="<p>Body one</p>", title="Post One"),
        ]

        result = engine.render(template, context={"posts": posts})

        assert "<h2>Post One</h2>" in result
        assert "<p>Body one</p>" in result

    def test_renders_without_context(self):
        engine = self._make_engine()
        template = "<p>Static content</p>"

        result = engine.render(template)

        assert "<p>Static content</p>" in result

    def test_jinja2_rendered_before_components(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Header"],
        )
        template = (
            "<Header />\n{% for post in posts %}<p>{{ post.title }}</p>{% endfor %}"
        )
        header_html = "<header>Site Header</header>"

        posts = [MarkdownContent(filename="", html="<p>a</p>", title="My Post")]

        with patch(f"{TEST_PATH}.open", mock_open(read_data=header_html)):
            result = engine.render(template, context={"posts": posts})

        assert "<header>Site Header</header>" in result
        assert "<p>My Post</p>" in result


class TestSiteConfigInTemplates:
    def test_site_name_available_in_template(self):
        config = SiteConfig(name="My Blog")
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=[],
            config=config,
        )
        template = "<title>{{ site.name }}</title>"

        result = engine.render(template)

        assert "<title>My Blog</title>" in result

    def test_site_url_available_in_template(self):
        config = SiteConfig(url="https://example.com")
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=[],
            config=config,
        )
        template = '<link rel="canonical" href="{{ site.url }}" />'

        result = engine.render(template)

        assert 'href="https://example.com"' in result

    def test_site_description_available_in_template(self):
        config = SiteConfig(description="A great blog")
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=[],
            config=config,
        )
        template = '<meta name="description" content="{{ site.description }}" />'

        result = engine.render(template)

        assert 'content="A great blog"' in result

    def test_site_authors_available_in_template(self):
        config = SiteConfig(
            authors=[
                AuthorConfig(name="Alice", email="alice@example.com"),
                AuthorConfig(name="Bob", email="bob@example.com"),
            ]
        )
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=[],
            config=config,
        )
        template = (
            "{% for author in site.authors %}<span>{{ author.name }}</span>{% endfor %}"
        )

        result = engine.render(template)

        assert "<span>Alice</span>" in result
        assert "<span>Bob</span>" in result

    def test_site_config_and_content_available_together(self):
        config = SiteConfig(name="My Blog")
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=[],
            config=config,
        )
        template = "<h1>{{ site.name }}</h1>{% for post in content %}<p>{{ post.title }}</p>{% endfor %}"
        posts = [MarkdownContent(filename="", html="<p>a</p>", title="Post One")]

        result = engine.render(template, context={"content": posts})

        assert "<h1>My Blog</h1>" in result
        assert "<p>Post One</p>" in result

    def test_no_config_renders_without_site_variable(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=[],
        )
        template = "<p>Static content</p>"

        result = engine.render(template)

        assert "<p>Static content</p>" in result
