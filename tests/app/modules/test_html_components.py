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

    def test_self_closing_has_empty_children(self):
        html = "<Alert />"
        matches = find_component_tags(html, {"Alert"})

        assert matches[0].children == ""


class TestFindComponentTagsOpenClose:
    def test_finds_open_close_component(self):
        html = "<Card><p>Hello</p></Card>"
        matches = find_component_tags(html, {"Card"})

        assert len(matches) == 1
        assert matches[0].name == "Card"

    def test_open_close_extracts_children(self):
        html = "<Card><p>Hello</p></Card>"
        matches = find_component_tags(html, {"Card"})

        assert matches[0].children == "<p>Hello</p>"

    def test_open_close_with_attrs_and_children(self):
        html = '<Card type="info"><p>Hello</p></Card>'
        matches = find_component_tags(html, {"Card"})

        assert matches[0].attrs == {"type": "info"}
        assert matches[0].children == "<p>Hello</p>"

    def test_open_close_captures_correct_start_and_end(self):
        html = "before<Card><p>Hi</p></Card>after"
        matches = find_component_tags(html, {"Card"})

        assert matches[0].start == 6
        assert matches[0].end == len("before<Card><p>Hi</p></Card>")

    def test_nested_same_component_extracts_outer_children(self):
        html = "<Card><Card>inner</Card></Card>"
        matches = find_component_tags(html, {"Card"})

        assert len(matches) == 1
        assert matches[0].children == "<Card>inner</Card>"

    def test_open_close_multiline_children(self):
        html = "<Layout>\n  <h1>Title</h1>\n  <p>Body</p>\n</Layout>"
        matches = find_component_tags(html, {"Layout"})

        assert matches[0].children == "\n  <h1>Title</h1>\n  <p>Body</p>\n"

    def test_open_close_no_attributes_no_children(self):
        html = "<Card></Card>"
        matches = find_component_tags(html, {"Card"})

        assert len(matches) == 1
        assert matches[0].attrs == {}
        assert matches[0].children == ""

    def test_finds_open_close_and_self_closing_in_sequence(self):
        html = "<Header /><Card><p>content</p></Card><Footer />"
        matches = find_component_tags(html, {"Header", "Card", "Footer"})

        assert len(matches) == 3
        names = [m.name for m in matches]
        assert "Header" in names
        assert "Card" in names
        assert "Footer" in names
        card = next(m for m in matches if m.name == "Card")
        assert card.children == "<p>content</p>"


class TestFindComponentTagsDotSyntax:
    def test_finds_dot_syntax_self_closing(self):
        html = "<UI.Card />"
        matches = find_component_tags(html, {"UI.Card"})

        assert len(matches) == 1
        assert matches[0].name == "UI.Card"

    def test_dot_syntax_with_attrs(self):
        html = '<UI.Card type="info" />'
        matches = find_component_tags(html, {"UI.Card"})

        assert matches[0].attrs == {"type": "info"}

    def test_dot_syntax_open_close_with_children(self):
        html = "<UI.Card><p>Content</p></UI.Card>"
        matches = find_component_tags(html, {"UI.Card"})

        assert matches[0].children == "<p>Content</p>"

    def test_dot_syntax_does_not_match_partial_names(self):
        html = "<UI.CardExtra />"
        matches = find_component_tags(html, {"UI.Card"})

        assert matches == []

    def test_deep_dot_syntax(self):
        html = "<A.B.C />"
        matches = find_component_tags(html, {"A.B.C"})

        assert len(matches) == 1
        assert matches[0].name == "A.B.C"


class TestReplaceComponentTags:
    def test_replaces_single_match(self):
        html = "before<Alert />after"
        matches = find_component_tags(html, {"Alert"})

        result = replace_component_tags(html, matches, ["<div>rendered</div>"])

        assert result == "before<div>rendered</div>after"

    def test_replaces_multiple_matches(self):
        html = "<Header /><main>hi</main><Footer />"
        matches = find_component_tags(html, {"Header", "Footer"})
        # sort matches by start position for deterministic ordering
        matches_ordered = sorted(matches, key=lambda m: m.start)
        replacements = ["<header>H</header>", "<footer>F</footer>"]

        result = replace_component_tags(html, matches_ordered, replacements)

        assert result == "<header>H</header><main>hi</main><footer>F</footer>"

    def test_returns_original_when_no_matches(self):
        html = "<div>hello</div>"

        result = replace_component_tags(html, [], [])

        assert result == html

    def test_preserves_surrounding_content(self):
        html = "<p>before</p><Widget /><p>after</p>"
        matches = find_component_tags(html, {"Widget"})

        result = replace_component_tags(html, matches, ["<span>W</span>"])

        assert "<p>before</p>" in result
        assert "<span>W</span>" in result
        assert "<p>after</p>" in result

    def test_replaces_two_instances_of_same_component_independently(self):
        html = '<Alert msg="a" /><Alert msg="b" />'
        matches = find_component_tags(html, {"Alert"})

        result = replace_component_tags(html, matches, ["<div>A</div>", "<div>B</div>"])

        assert result == "<div>A</div><div>B</div>"

    def test_replaces_open_close_match(self):
        html = "<Card><p>Hello</p></Card>"
        matches = find_component_tags(html, {"Card"})

        result = replace_component_tags(html, matches, ["<div>rendered</div>"])

        assert result == "<div>rendered</div>"
