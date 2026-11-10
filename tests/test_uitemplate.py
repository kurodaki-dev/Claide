import pytest

import claide.uitemplate as ui
from claide import Page, UITemplate, UITemplateError
from claide.uitemplate import parse_uiverse_id

SOURCE = """<button class="cta"><span>Contact Us</span></button>

<style>
/* From Uiverse.io by someone  - Tags: button, hover */
.cta { color: red; }
.cta span { color: blue; }
.cta-other { color: green; }
</style>
"""

TAILWIND = """<!-- From Uiverse.io by tw  - Tags: card -->
<div class="relative w-48 h-64 rounded-xl bg-[#3d3c3d]">CARD</div>"""


@pytest.fixture(autouse=True)
def fake_github(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAIDE_CACHE_DIR", str(tmp_path))
    calls = []

    def fake_download(url, timeout):
        calls.append(url)
        if url.endswith("/Buttons/someone_cool-cat-1.html"):
            return SOURCE
        if url.endswith("/Cards/tw_card-2.html"):
            return TAILWIND
        return None

    monkeypatch.setattr(ui, "_download", fake_download)
    return calls


@pytest.mark.parametrize("ref", [
    "someone/cool-cat-1",
    "https://uiverse.io/someone/cool-cat-1",
    "https://uiverse.io/someone/cool-cat-1?x=1",
    "someone_cool-cat-1",
    "Buttons/someone_cool-cat-1.html",
])
def test_parse_id(ref):
    assert parse_uiverse_id(ref) == ("someone", "cool-cat-1")


def test_fetch_and_render(fake_github):
    tpl = UITemplate("https://uiverse.io/someone/cool-cat-1")
    assert tpl.category == "Buttons"
    assert tpl.tags == ["button", "hover"]
    assert "<style>" not in tpl.html
    html = Page("x", tpl).render()
    assert ".cta { color: red; }" in html
    assert '<button class="cta">' in html
    # mise en cache : pas de nouvel appel réseau
    n = len(fake_github)
    UITemplate("someone/cool-cat-1")
    assert len(fake_github) == n


def test_customize():
    tpl = UITemplate("someone/cool-cat-1").text("Contact Us", "<Go>").attrs(id="b", class_="big", onclick="f()")
    assert '<button class="cta big" id="b" onclick="f()">' in tpl.html
    assert "&lt;Go&gt;" in tpl.html
    linked = tpl.link("/contact")
    assert linked.html.startswith('<a href="/contact"')


def test_scoped_does_not_touch_other_classes():
    tpl = UITemplate("someone/cool-cat-1").prefix("x-")
    assert 'class="x-cta"' in tpl.html
    assert ".x-cta span" in tpl.css
    assert ".cta-other" in tpl.css  # classe absente du HTML : inchangée


def test_tailwind_detection():
    tpl = UITemplate("tw/card-2", category="card")
    assert tpl.tailwind
    assert "cdn.tailwindcss.com" in Page("x", tpl).render().split("</head>")[0]


def test_not_found():
    with pytest.raises(UITemplateError):
        UITemplate("nobody/nothing-0")


def test_manual_and_builtin():
    tpl = UITemplate(html="<button class='b'>OK</button>", css=".b{color:red}")
    assert ".b{color:red}" in Page("x", tpl).render()
    b = UITemplate.builtin("glow", "Envoyer")
    assert "Envoyer" in b.html and ".cl-glow" in b.css
    with pytest.raises(UITemplateError):
        UITemplate.builtin("inconnu")


def test_import_style():
    from claide import uitemplate
    assert uitemplate.UITemplate is UITemplate
