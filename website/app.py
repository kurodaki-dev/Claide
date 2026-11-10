"""Claide's own website and documentation — built with Claide.

Run locally:      python website/app.py        -> http://127.0.0.1:8000
Static export:    python website/app.py build  -> website/_site/
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # use the local claide

from claide import App, Element, Page, UITemplate, __version__, tags as t  # noqa: E402

from mdlite import render as render_markdown  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = "https://github.com/kurodaki-dev/Claide"
PYPI = "https://pypi.org/project/claide-web/"
HLJS = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0"

app = App(__name__, title="Claide", base_path=os.environ.get("BASE_PATH", ""))
app.css(
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap",
    f"{HLJS}/styles/github-dark.min.css",
    app.static("style.css"),
)
app.js(f"{HLJS}/highlight.min.js", app.static("main.js"))
url = app.url


# ---------------------------------------------------------------------------
# Documentation pages (website/content/NN-slug.md)
# ---------------------------------------------------------------------------
class Doc:
    def __init__(self, path: Path) -> None:
        self.slug = path.stem.split("-", 1)[1]
        self.title, self.html, self.toc = render_markdown(path.read_text(encoding="utf-8"), url)
        self.summary = next(
            (line.strip() for line in path.read_text(encoding="utf-8").splitlines()[1:]
             if line.strip() and not line.startswith(("#", "`", "|", ">", "-"))), ""
        )

    @property
    def href(self) -> str:
        return url(f"/docs/{self.slug}")


DOCS = [Doc(p) for p in sorted((HERE / "content").glob("*.md"))]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
LOGO = t.span(t.span("✦", class_="logo-mark"), "claide", class_="logo")


def header(active: str = "") -> Element:
    links = [("Docs", url("/docs"), "docs"), ("Showcase", url("/#showcase"), "showcase"),
             ("PyPI", PYPI, ""), ("GitHub", REPO, "")]
    return t.header(
        t.div(
            t.a(LOGO, href=url("/"), class_="brand", aria_label="Claide home"),
            t.nav(t.ul([
                t.li(t.a(label, href=href, aria_current="page" if key and key == active else None))
                for label, href, key in links
            ])),
            t.span(f"v{__version__}", class_="version"),
            class_="wrap header-inner",
        ),
        class_="site-header",
    )


def footer() -> Element:
    return t.footer(t.div(
        t.p(LOGO, " — build complete websites in Python. MIT license."),
        t.p("This website is a Claide app, exported with ", t.code("app.build()"), "."),
        t.p(t.a("GitHub", href=REPO), " · ", t.a("PyPI", href=PYPI), " · ",
            t.a("Uiverse.io", href="https://uiverse.io")),
        class_="wrap",
    ), class_="site-footer")


def page(title: str, *content, active: str = "", description: str = "") -> Page:
    p = Page(
        f"{title} · Claide" if title != "Claide" else "Claide — websites in Python",
        header(active), t.main(*content), footer(),
        description=description or "Claide: build complete websites in Python, with Uiverse.io components.",
        favicon=app.static("favicon.svg"),
    )
    p.meta(name="theme-color", content="#6d28d9")
    return p


def code_block(code: str, lang: str = "python") -> Element:
    return t.pre(t.code(code.strip("\n"), class_=f"language-{lang}"))


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
HELLO = '''
from claide import App, Page, UITemplate, tags as t

app = App(__name__)
button = UITemplate("0x-Sarthak/hungry-penguin-30")

@app.route("/")
def home():
    return Page(
        "Home",
        t.h1("Hello!"),
        button.link("/contact"),
    )

app.run()
'''

FEATURES = [
    ("🐍", "100% Python", "Pages, components and server in plain Python. No template language, no dependencies."),
    ("🎨", "Uiverse built in", "Use any of the 3,000+ Uiverse.io / cssbuttons.io components in one line."),
    ("⚡", "Dynamic server", "Routes, forms, uploads, JSON APIs, sessions, cookies, hooks and streaming."),
    ("📎", "Your CSS & JS", "Link style.css and script.js on every page or a single one, or inline them."),
    ("🧱", "Ready-made blocks", "Navbar, hero, cards, grid, forms and alerts with a clean default theme."),
    ("🚀", "Deploy anywhere", "WSGI for gunicorn & co, or export a static site for GitHub Pages."),
]

UIVERSE_SHOWCASE = [
    ("0x-Sarthak/hungry-penguin-30", "Buttons"),
    ("adamgiebl/big-moose-23", "Buttons"),
    ("Bethel-nz/honest-elephant-63", "loaders"),
    ("ErzenXz/weak-falcon-28", "Toggle-switches"),
]


def showcase_items():
    items = []
    for name in ("gradient", "glow", "slide", "pushable", "spinner", "toggle"):
        items.append((UITemplate.builtin(name), f'UITemplate.builtin("{name}")'))
    for ref, category in UIVERSE_SHOWCASE:
        try:
            items.append((UITemplate(ref, category=category).scoped(), f'UITemplate("{ref}")'))
        except Exception as exc:  # no network: the build must not fail
            print(f"[showcase] skipped {ref}: {exc}", file=sys.stderr)
    return items


SHOWCASE = showcase_items()


@app.route("/")
def home():
    return page(
        "Claide",
        t.section(t.div(
            t.div(
                t.p("Python web framework · Uiverse components", class_="eyebrow"),
                t.h1("Build complete websites in ", t.span("Python", class_="grad"), "."),
                t.p("Pages, routes, forms, APIs, sessions, your own CSS & JS, and thousands of "
                    "Uiverse.io components — all from one tiny module with zero dependencies.", class_="lead"),
                t.div(
                    t.a("Read the docs →", href=url("/docs/getting-started"), class_="btn btn-primary"),
                    t.a("GitHub", href=REPO, class_="btn btn-ghost"),
                    class_="actions",
                ),
                t.div(t.code("$ pip install claide-web"),
                      t.button("Copy", class_="copy", data_copy="pip install claide-web"), class_="install"),
                class_="hero-text",
            ),
            t.div(t.div(t.span(), t.span(), t.span(), t.em("app.py"), class_="window-bar"),
                  code_block(HELLO), class_="window"),
            class_="wrap hero-inner",
        ), class_="hero"),

        t.section(t.div(
            t.h2("Everything you need for a website"),
            t.div([t.div(t.div(icon, class_="feature-icon"), t.h3(title), t.p(text), class_="feature")
                   for icon, title, text in FEATURES], class_="features"),
            class_="wrap",
        ), class_="section"),

        t.section(t.div(
            t.h2("Components showcase"),
            t.p("Live components rendered by Claide. Built-in ones work offline; Uiverse ones are "
                "fetched from the official archive and cached.", class_="section-lead"),
            t.div([t.figure(t.div(tpl, class_="demo-stage"), t.figcaption(t.code(label)))
                   for tpl, label in SHOWCASE], class_="showcase"),
            class_="wrap",
        ), class_="section section-alt", id="showcase"),

        t.section(t.div(
            t.h2("Start in 10 seconds"),
            t.div(
                code_block("pip install claide-web\nclaide new mysite\ncd mysite\npython app.py", "bash"),
                t.div(
                    t.p("The ", t.code("claide new"), " command creates a project with a navbar, a contact "
                        "form, a JSON route, sessions, and linked ", t.code("style.css"), " / ",
                        t.code("script.js"), " files. Edit and save: the server reloads by itself."),
                    t.a("Getting started →", href=url("/docs/getting-started"), class_="btn btn-primary"),
                ),
                class_="split",
            ),
            class_="wrap",
        ), class_="section"),
    )


# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------
def docs_sidebar(current: str = "") -> Element:
    return t.aside(
        t.button("Menu", class_="sidebar-toggle", aria_expanded="false"),
        t.nav(
            t.p("Documentation", class_="sidebar-title"),
            t.ul([t.li(t.a(d.title, href=d.href, aria_current="page" if d.slug == current else None))
                  for d in DOCS]),
            class_="sidebar-nav",
        ),
        class_="sidebar",
    )


@app.route("/docs")
def docs_index():
    return page("Documentation", t.div(
        docs_sidebar(),
        t.article(
            t.h1("Documentation"),
            t.p("Everything about Claide, from your first page to deployment.", class_="section-lead"),
            t.div([t.a(t.h3(d.title), t.p(d.summary), href=d.href, class_="doc-card") for d in DOCS],
                  class_="doc-grid"),
            class_="doc",
        ),
        class_="wrap docs",
    ), active="docs")


def make_doc_view(index: int):
    doc = DOCS[index]
    prev_doc = DOCS[index - 1] if index > 0 else None
    next_doc = DOCS[index + 1] if index + 1 < len(DOCS) else None

    def view():
        return page(doc.title, t.div(
            docs_sidebar(doc.slug),
            t.article(
                doc.html,
                t.nav(
                    t.a(t.small("Previous"), t.span(prev_doc.title), href=prev_doc.href, class_="pager-prev")
                    if prev_doc else t.span(),
                    t.a(t.small("Next"), t.span(next_doc.title), href=next_doc.href, class_="pager-next")
                    if next_doc else t.span(),
                    class_="pager",
                ),
                class_="doc",
            ),
            t.aside(
                t.p("On this page", class_="sidebar-title"),
                t.ul([t.li(t.a(text, href=f"#{hid}")) for hid, text in doc.toc]),
                class_="toc",
            ) if doc.toc else None,
            class_="wrap docs",
        ), active="docs", description=doc.summary)

    view.__name__ = f"doc_{doc.slug.replace('-', '_')}"
    return view


for i, d in enumerate(DOCS):
    app.add_route(f"/docs/{d.slug}", make_doc_view(i))


@app.errorhandler(404)
def not_found():
    return page("Not found", t.section(t.div(
        t.h1("404"), t.p("This page does not exist."),
        t.a("Back home", href=url("/"), class_="btn btn-primary"),
        class_="wrap center",
    ), class_="section"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        out = sys.argv[2] if len(sys.argv) > 2 else str(HERE / "_site")
        written = app.build(out)
        Path(out, ".nojekyll").touch()
        print(f"Built {len(written)} pages into {out}")
    else:
        app.run()
