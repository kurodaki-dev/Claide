"""Claide's own website and documentation, built with Claide.

Run locally:      python website/app.py        -> http://127.0.0.1:8000
Static export:    python website/app.py build  -> website/_site/
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # use the local claide

from claide import App, Element, Page, UITemplate, __version__, tags as t  # noqa: E402

from claide.markdown import render as render_markdown  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = "https://github.com/kurodaki-dev/Claide"
PYPI = "https://pypi.org/project/claide-web/"
HLJS = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0"
FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=IBM+Plex+Mono:wght@400;500&"
    "family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&"
    "family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap"
)

app = App(__name__, title="Claide", base_path=os.environ.get("BASE_PATH", ""))
app.css(FONTS, app.static("style.css"))
app.js(f"{HLJS}/highlight.min.js", app.static("main.js"))
url = app.url


# ---------------------------------------------------------------------------
# Documentation pages (website/content/NN-slug.md)
# ---------------------------------------------------------------------------
SUMMARIES = {
    "getting-started": "Install Claide, write a first page and create a project with claide new.",
    "pages-and-html": "Build HTML with tags, assemble complete pages and write reusable pieces.",
    "routing": "Routes, URL parameters, the request object, routers and hooks.",
    "responses": "What a route can return: pages, JSON, redirects, errors, files and streams.",
    "forms-sessions": "Read forms, receive uploaded files, and keep state in sessions and cookies.",
    "static-files": "Serve the static folder and link CSS and JavaScript on one page or all of them.",
    "uiverse": "Use any Uiverse.io or cssbuttons.io element, customize it and isolate its CSS.",
    "components": "Navbar, hero, cards, grid, forms and alerts, and how to theme them.",
    "cli": "The claide command: new, run, build and ui.",
    "deployment": "Run in production with WSGI, export a static site, deploy to GitHub Pages.",
    "testing": "Test routes, forms and APIs with the built-in test client.",
}


class Doc:
    def __init__(self, path: Path) -> None:
        self.slug = path.stem.split("-", 1)[1]
        self.title, self.html, self.toc = render_markdown(path.read_text(encoding="utf-8"), url)
        self.summary = SUMMARIES.get(self.slug, "")

    @property
    def href(self) -> str:
        return url(f"/docs/{self.slug}")


DOCS = [Doc(p) for p in sorted((HERE / "content").glob("*.md"))]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def header(active: str = "") -> Element:
    links = [("Documentation", url("/docs"), "docs"), ("Components", url("/#components"), ""),
             ("GitHub", REPO, ""), ("PyPI", PYPI, "")]
    return t.header(
        t.div(
            t.a("claide", href=url("/"), class_="wordmark"),
            t.span(f"v{__version__}", class_="version"),
            t.nav(t.ul([
                t.li(t.a(label, href=href, aria_current="page" if key and key == active else None))
                for label, href, key in links
            ]), aria_label="Main"),
            class_="wrap header-inner",
        ),
        class_="site-header",
    )


def footer() -> Element:
    return t.footer(t.div(
        t.p(t.span("claide", class_="wordmark"), " is free software under the MIT license."),
        t.p("This site is a Claide app exported with ", t.code("app.build()"),
            ". Its source is in ", t.a("website/", href=f"{REPO}/tree/main/website"), "."),
        class_="wrap",
    ), class_="site-footer")


def page(title: str, *content, active: str = "", description: str = "") -> Page:
    p = Page(
        f"{title} · Claide" if title != "Claide" else "Claide: websites in plain Python",
        header(active), t.main(*content), footer(),
        description=description or "Claide is a Python module to build complete websites, "
                                   "with Uiverse.io components built in.",
        favicon=app.static("favicon.svg"),
    )
    return p


def code_block(code: str, lang: str = "python", caption: str = "") -> Element:
    block = t.pre(t.code(code.strip("\n"), class_=f"language-{lang}"))
    if not caption:
        return block
    return t.figure(t.figcaption(caption), block, class_="code-figure")


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
HELLO = '''
from claide import *

@route("/")
def home():
    return h1("Hello!"), p("Welcome to my site.")

@route("/contact")
def contact(name: str = ""):
    if request.method == "POST":
        return h1(f"Thanks {name}!")
    return h1("Contact"), form(
        input_(name="name"),
        button("Send"),
        method="post",
    )

run()
'''

FEATURES = [
    ("Pages", "h1(), p(), div(), form()... every tag is a function. Return a few elements "
              "and Claide builds the page, with a clean default style."),
    ("Routing", "Form and URL values arrive as typed parameters. Sessions, cookies, uploads "
                "and JSON responses work without setup."),
    ("Uiverse components", "Paste the URL of any element from uiverse.io or cssbuttons.io. "
                           "Its CSS is added to the page and kept out of the rest of your site."),
    ("Your own files", "Put style.css, script.js and a favicon in static/: they are used on "
                       "every page without writing a line."),
    ("No dependencies", "Only the standard library. The development server reloads when "
                        "you save; any WSGI server runs it in production."),
    ("Static export", "app.build() writes plain HTML files you can host anywhere. "
                      "This website is made that way."),
]

SHOWCASE_BUILTIN = ["gradient", "glow", "slide", "pushable", "spinner", "toggle"]
SHOWCASE_UIVERSE = [
    ("0x-Sarthak/hungry-penguin-30", "Buttons"),
    ("adamgiebl/big-moose-23", "Buttons"),
    ("Bethel-nz/honest-elephant-63", "loaders"),
    ("ErzenXz/weak-falcon-28", "Toggle-switches"),
]


def showcase_items():
    items = [(UITemplate.builtin(name), f'builtin("{name}")') for name in SHOWCASE_BUILTIN]
    for ref, category in SHOWCASE_UIVERSE:
        try:
            items.append((UITemplate(ref, category=category).scoped(), ref))
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
                t.h1("Websites in plain Python."),
                t.p("Every HTML tag is a function, form fields arrive as parameters, and your "
                    "CSS and JavaScript are linked by themselves. Routes, sessions, APIs and "
                    "Uiverse.io components included, with no dependencies.", class_="lead"),
                t.div(
                    t.a("Read the documentation", href=url("/docs/getting-started"), class_="button"),
                    t.a("Source on GitHub", href=REPO, class_="text-link"),
                    class_="actions",
                ),
                t.p(t.code("pip install claide-web"),
                    t.button("Copy", type="button", class_="copy", data_copy="pip install claide-web"),
                    class_="install"),
                class_="intro",
            ),
            code_block(HELLO, caption="app.py"),
            class_="wrap hero-grid",
        ), class_="hero"),

        t.section(t.div(
            t.h2("What it does"),
            t.dl([t.div(t.dt(term), t.dd(text)) for term, text in FEATURES], class_="features"),
            class_="wrap",
        ), class_="band"),

        t.section(t.div(
            t.div(
                t.h2("Components"),
                t.p("The first six ship with Claide and work offline. The others are taken "
                    "from the Uiverse archive the first time they are used, then cached.",
                    class_="section-note"),
                class_="band-head",
            ),
            t.div([t.figure(t.div(tpl, class_="specimen"), t.figcaption(t.code(label), title=label))
                   for tpl, label in SHOWCASE], class_="showcase"),
            class_="wrap",
        ), class_="band", id="components"),

        t.section(t.div(
            t.div(
                t.h2("Getting started"),
                t.p(t.code("claide new"), " creates a small project: a navigation bar, a contact "
                    "form, a JSON route, a session counter and a ", t.code("static"), " folder for "
                    "your CSS and JavaScript."),
                t.p(t.a("Continue with the guide", href=url("/docs/getting-started"), class_="text-link")),
            ),
            code_block("pip install claide-web\nclaide new mysite\ncd mysite\npython app.py", "bash",
                       caption="terminal"),
            class_="wrap two-col",
        ), class_="band"),
    )


# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------
def docs_sidebar(current: str = "") -> Element:
    return t.aside(
        t.button("Contents", type="button", class_="sidebar-toggle", aria_expanded="false"),
        t.nav(
            t.ol([t.li(t.a(d.title, href=d.href, aria_current="page" if d.slug == current else None))
                  for d in DOCS]),
            class_="sidebar-nav", aria_label="Documentation",
        ),
        class_="sidebar",
    )


@app.route("/docs")
def docs_index():
    return page("Documentation", t.div(
        docs_sidebar(),
        t.article(
            t.h1("Documentation"),
            t.p("From a first page to deployment. The chapters are short and can be read in order.",
                class_="lead"),
            t.ol([t.li(t.a(d.title, href=d.href), t.span(d.summary)) for d in DOCS], class_="chapters"),
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
                    class_="pager", aria_label="Chapters",
                ),
                class_="doc",
            ),
            t.aside(
                t.p("On this page", class_="toc-title"),
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
        t.h1("Page not found"),
        t.p("There is nothing at this address. ", t.a("Go to the home page", href=url("/")), "."),
        class_="wrap narrow",
    ), class_="band"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        out = sys.argv[2] if len(sys.argv) > 2 else str(HERE / "_site")
        written = app.build(out)
        Path(out, ".nojekyll").touch()
        print(f"Built {len(written)} pages into {out}")
    else:
        app.run()
