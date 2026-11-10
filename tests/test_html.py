from claide import Element, Page, raw, tags as t


def test_tags_and_attrs():
    el = t.div(t.h1("Hello"), class_="hero", data_id=3, hidden=True, disabled=False)
    assert str(el) == '<div class="hero" data-id="3" hidden><h1>Hello</h1></div>'


def test_escape_and_raw():
    assert str(t.p("<b>")) == "<p>&lt;b&gt;</p>"
    assert str(t.p(raw("<b>ok</b>"))) == "<p><b>ok</b></p>"


def test_void_and_style_dict():
    assert str(t.img(src="a.png", style={"max_width": "10px"})) == '<img src="a.png" style="max-width: 10px">'


def test_custom_tag_and_lists():
    assert str(t.my_widget([t.li(i) for i in range(2)])) == "<my-widget><li>0</li><li>1</li></my-widget>"


def test_page_assets_dedup():
    child = Element("div").with_css(".a{}").with_js("go()")
    page = Page("T", child, child).css("/s.css", "/s.css").js("/s.js")
    html = page.render()
    assert html.startswith("<!DOCTYPE html>")
    assert html.count('href="/s.css"') == 1
    assert html.count(".a{}") == 1
    assert html.index('src="/s.js"') > html.index("<body")
    assert "<title>T</title>" in html and 'lang="en"' in html


def test_base_css_removes_tap_highlight():
    html = Page("T").css("/mine.css").render()
    assert "-webkit-tap-highlight-color: transparent" in html
    assert ":focus:not(:focus-visible) { outline: none; }" in html
    # the reset comes before the page's own stylesheets so they can override it
    assert html.index("tap-highlight") < html.index('href="/mine.css"')
    assert "tap-highlight" not in Page("T", base_css=False).render()
