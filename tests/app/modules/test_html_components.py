from pyssg.modules.html import find_component_tags, replace_component_tags


class TestFindComponentTags:
    def test_finds_single_component(self):
        html = '<Navbar homeClass="active" />'
        matches = find_component_tags(html, {"Navbar"})

        assert len(matches) == 1
        assert matches[0].name == "Navbar"
        assert matches[0].attrs == {"homeClass": "active"}

    def test_finds_multiple_components(self):
        html = "<Header />\n<main>Content</main>\n<Footer />"
        matches = find_component_tags(html, {"Header", "Footer"})

        assert len(matches) == 2
        assert matches[0].name == "Header"
        assert matches[1].name == "Footer"

    def test_skips_unknown_tags(self):
        html = '<Unknown prop="val" /><Navbar />'
        matches = find_component_tags(html, {"Navbar"})

        assert len(matches) == 1
        assert matches[0].name == "Navbar"

    def test_returns_empty_list_when_no_matches(self):
        html = "<div>Hello</div>"
        matches = find_component_tags(html, {"Navbar"})

        assert matches == []

    def test_captures_start_and_end_positions(self):
        html = "before<Alert />after"
        matches = find_component_tags(html, {"Alert"})

        assert matches[0].start == 6
        assert matches[0].end == 15

    def test_handles_component_without_space_before_close(self):
        html = "<Divider/>"
        matches = find_component_tags(html, {"Divider"})

        assert len(matches) == 1
        assert matches[0].name == "Divider"

    def test_handles_multiple_attributes(self):
        html = '<Alert type="info" title="Note" message="Hello" />'
        matches = find_component_tags(html, {"Alert"})

        assert matches[0].attrs == {
            "type": "info",
            "title": "Note",
            "message": "Hello",
        }

    def test_skips_regular_html_tags(self):
        html = '<div class="foo" /><Navbar />'
        matches = find_component_tags(html, {"Navbar"})

        assert len(matches) == 1
        assert matches[0].name == "Navbar"

    def test_empty_html_returns_empty(self):
        matches = find_component_tags("", {"Navbar"})

        assert matches == []

    def test_empty_component_set_returns_empty(self):
        matches = find_component_tags("<Navbar />", set())

        assert matches == []


class TestReplaceComponentTags:
    def test_replaces_single_match(self):
        html = "before<Alert />after"
        matches = find_component_tags(html, {"Alert"})
        replacements = {"Alert": "<div>rendered</div>"}

        result = replace_component_tags(html, matches, replacements)

        assert result == "before<div>rendered</div>after"

    def test_replaces_multiple_matches(self):
        html = "<Header /><main>hi</main><Footer />"
        matches = find_component_tags(html, {"Header", "Footer"})
        replacements = {
            "Header": "<header>H</header>",
            "Footer": "<footer>F</footer>",
        }

        result = replace_component_tags(html, matches, replacements)

        assert result == "<header>H</header><main>hi</main><footer>F</footer>"

    def test_returns_original_when_no_matches(self):
        html = "<div>hello</div>"

        result = replace_component_tags(html, [], {})

        assert result == html

    def test_preserves_surrounding_content(self):
        html = "<p>before</p><Widget /><p>after</p>"
        matches = find_component_tags(html, {"Widget"})
        replacements = {"Widget": "<span>W</span>"}

        result = replace_component_tags(html, matches, replacements)

        assert "<p>before</p>" in result
        assert "<span>W</span>" in result
        assert "<p>after</p>" in result
