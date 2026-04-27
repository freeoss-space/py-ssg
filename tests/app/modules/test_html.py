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

    def test_builtin_post_url_global(self):
        engine = self._make_engine()
        post = MarkdownContent(filename="blog/hello-world.md", html="<p>Hello</p>")

        result = engine.render("{{ post_url(post) }}", context={"post": post})

        assert result == "/blog/hello-world/"

    def test_builtin_is_blog_post_global(self):
        engine = self._make_engine()
        post = MarkdownContent(filename="blog/hello-world.md", html="<p>Hello</p>")

        result = engine.render(
            "{% if is_blog_post(post) %}yes{% else %}no{% endif %}",
            context={"post": post},
        )

        assert result == "yes"

    def test_builtin_slug_filter(self):
        engine = self._make_engine()

        result = engine.render("{{ 'Hello, World!'|slug }}")

        assert result == "hello-world"

    def test_builtin_date_format_filter(self):
        engine = self._make_engine()

        result = engine.render("{{ '2025-01-15T12:30:00'|date_format('%Y-%m') }}")

        assert result == "2025-01"

    def test_builtin_excerpt_filter(self):
        engine = self._make_engine()

        result = engine.render(
            "{{ '<p>Hello <strong>world</strong> again</p>'|excerpt(11) }}"
        )

        assert result == "Hello wo..."


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


class TestComponentChildren:
    def test_component_receives_children_content(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Card"],
        )
        template = "<Card><p>Hello</p></Card>"
        card_html = "<div class='card'>{{ children }}</div>"

        with patch(f"{TEST_PATH}.open", mock_open(read_data=card_html)):
            result = engine.render(template)

        assert "<p>Hello</p>" in result
        assert "class='card'" in result

    def test_component_children_empty_string_when_self_closing(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Card"],
        )
        template = "<Card />"
        card_html = "<div>{{ children }}</div>"

        with patch(f"{TEST_PATH}.open", mock_open(read_data=card_html)):
            result = engine.render(template)

        assert "<div></div>" in result

    def test_nested_components_with_children(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Layout", "Card"],
        )
        template = "<Layout><Card /></Layout>"
        layout_html = "<main>{{ children }}</main>"
        card_html = "<div>Card Content</div>"

        def side_effect(path, *args, **kwargs):
            content = {
                "/components/Layout.html": layout_html,
                "/components/Card.html": card_html,
            }
            return mock_open(read_data=content[str(path)])()

        with patch(f"{TEST_PATH}.open", side_effect=side_effect):
            result = engine.render(template)

        assert "<main>" in result
        assert "<div>Card Content</div>" in result

    def test_children_with_attributes_on_component(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Box"],
        )
        template = '<Box class="highlight"><span>text</span></Box>'
        box_html = '<section class="{{ class }}">{{ children }}</section>'

        with patch(f"{TEST_PATH}.open", mock_open(read_data=box_html)):
            result = engine.render(template)

        assert 'class="highlight"' in result
        assert "<span>text</span>" in result

    def test_two_sibling_components_with_different_children(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Box"],
        )
        template = "<Box><p>first</p></Box><Box><p>second</p></Box>"
        box_html = "<div>{{ children }}</div>"

        with patch(f"{TEST_PATH}.open", mock_open(read_data=box_html)):
            result = engine.render(template)

        assert "<p>first</p>" in result
        assert "<p>second</p>" in result


class TestComponentParentContext:
    def test_component_receives_site_and_parent_template_context(self):
        config = SiteConfig(name="My Blog")
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["Banner"],
            config=config,
        )
        template = "<Banner />"
        banner_html = "<header>{{ site.name }} {{ section }}</header>"

        with patch(f"{TEST_PATH}.open", mock_open(read_data=banner_html)):
            result = engine.render(template, context={"section": "News"})

        assert "<header>My Blog News</header>" in result


class TestDotSyntaxComponents:
    def test_dot_syntax_resolves_to_subdirectory(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["UI.Card"],
        )
        template = "<UI.Card />"
        card_html = "<div>Card</div>"

        def side_effect(path, *args, **kwargs):
            content = {
                "/components/UI/Card.html": card_html,
            }
            return mock_open(read_data=content[str(path)])()

        with patch(f"{TEST_PATH}.open", side_effect=side_effect):
            result = engine.render(template)

        assert "<div>Card</div>" in result

    def test_dot_syntax_with_children(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["UI.Card"],
        )
        template = "<UI.Card><p>content</p></UI.Card>"
        card_html = "<article>{{ children }}</article>"

        def side_effect(path, *args, **kwargs):
            content = {
                "/components/UI/Card.html": card_html,
            }
            return mock_open(read_data=content[str(path)])()

        with patch(f"{TEST_PATH}.open", side_effect=side_effect):
            result = engine.render(template)

        assert "<article>" in result
        assert "<p>content</p>" in result

    def test_deep_dot_syntax_resolves_nested_subdirectory(self):
        engine = HtmlTemplateEngine(
            templates_dir=Path("/templates"),
            components_dir=Path("/components"),
            component_names=["A.B.C"],
        )
        template = "<A.B.C />"
        component_html = "<span>deep</span>"

        def side_effect(path, *args, **kwargs):
            content = {
                "/components/A/B/C.html": component_html,
            }
            return mock_open(read_data=content[str(path)])()

        with patch(f"{TEST_PATH}.open", side_effect=side_effect):
            result = engine.render(template)

        assert "<span>deep</span>" in result
