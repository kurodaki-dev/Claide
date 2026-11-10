"""Command line: ``claide new``, ``claide run``, ``claide build``, ``claide ui``."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from typing import List, Optional

from . import __version__

APP_TEMPLATE = '''from claide import App, Page, UITemplate, tags as t
from claide.components import Navbar, Hero, Section, Grid, Card, Footer, Form, Field, Alert

app = App(__name__, secret_key="{secret}")
app.css(app.static("style.css"))
app.js(app.static("script.js"))

NAV = Navbar("{name}", [("Home", "/"), ("Contact", "/contact")])
button = UITemplate.builtin("gradient", "Get started")


@app.layout
def base(page):
    page.body.children.insert(0, NAV)
    page.add(Footer("Made with Claide 🐍"))


@app.route("/")
def home(request):
    visits = request.session.get("visits", 0) + 1
    request.session["visits"] = visits
    return Page(
        "{name}",
        Hero("Welcome to {name}", f"You have been here {{visits}} time(s).", button.link("/contact")),
        Section(
            Grid(
                Card("Fast", "100% Python, zero dependencies."),
                Card("Complete", "Routes, forms, APIs, sessions."),
                Card("Pretty", "Uiverse.io components built in."),
            ),
            title="Why Claide?",
        ),
    )


@app.route("/contact", methods=["GET", "POST"])
def contact(request):
    message = None
    if request.method == "POST":
        message = Alert(f"Thanks {{request.form.get('name', '')}}!", "success")
    return Page("Contact", Section(
        message,
        Form(Field("Name", "name", required=True), Field("Message", "message", type="textarea")),
        title="Contact",
    ))


@app.get("/api/hello/<name>")
def api_hello(name):
    return {{"message": f"Hello {{name}}!"}}


if __name__ == "__main__":
    app.run()
'''

CSS_TEMPLATE = """/* Your CSS here */
:root { --cl-primary: #6366f1; }
"""

JS_TEMPLATE = """// Your JavaScript here
console.log("Claide is ready ✦");
"""


def _load_app(target: str):
    """'app:app' or 'app.py' -> App object."""
    sys.path.insert(0, os.getcwd())
    module_name, _, attr = target.partition(":")
    if module_name.endswith(".py"):
        module_name = module_name[:-3].replace(os.sep, ".").replace("/", ".")
    module = importlib.import_module(module_name)
    app = getattr(module, attr or "app", None)
    if app is None:
        raise SystemExit(f"No object '{attr or 'app'}' in {module_name}")
    return app


def cmd_new(args: argparse.Namespace) -> None:
    import secrets

    root = args.name
    if os.path.exists(root) and os.listdir(root):
        raise SystemExit(f"The folder '{root}' already exists and is not empty.")
    os.makedirs(os.path.join(root, "static"), exist_ok=True)
    name = os.path.basename(os.path.abspath(root))
    files = {
        "app.py": APP_TEMPLATE.format(name=name, secret=secrets.token_hex(16)),
        os.path.join("static", "style.css"): CSS_TEMPLATE,
        os.path.join("static", "script.js"): JS_TEMPLATE,
    }
    for rel, content in files.items():
        with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"✦ Project created in {root}/\n\n  cd {root}\n  python app.py\n")


def cmd_run(args: argparse.Namespace) -> None:
    app = _load_app(args.app)
    app.debug = not args.prod
    from .server import run_server

    run_server(app, args.host, args.port, reload=False)


def cmd_build(args: argparse.Namespace) -> None:
    app = _load_app(args.app)
    written = app.build(args.out)
    print(f"✦ {len(written)} page(s) written to {args.out}/")


def cmd_ui(args: argparse.Namespace) -> None:
    from .uitemplate import UITemplate

    tpl = UITemplate(args.ref, category=args.category)
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(tpl.html + "\n\n<style>\n" + tpl.css + "\n</style>\n")
            if tpl.js:
                f.write("\n<script>\n" + tpl.js + "\n</script>\n")
        print(f"✦ Saved to {args.save}")
    elif args.preview:
        print(f"✦ Preview: {tpl.preview()}")
    else:
        print(f"<!-- {tpl!r} -->\n{tpl.html}\n\n<style>\n{tpl.css}\n</style>")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="claide", description="Build websites in Python.")
    parser.add_argument("--version", action="version", version=f"claide {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="Create a new project")
    p.add_argument("name")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("run", help="Run an app (e.g. claide run app:app)")
    p.add_argument("app", nargs="?", default="app:app")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--prod", action="store_true", help="Disable debug mode")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("build", help="Export pages as static HTML")
    p.add_argument("app", nargs="?", default="app:app")
    p.add_argument("--out", default="dist")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("ui", help="Download a Uiverse component (author/name or URL)")
    p.add_argument("ref")
    p.add_argument("--category", default=None)
    p.add_argument("--save", default=None, help="Output .html file")
    p.add_argument("--preview", action="store_true", help="Generate a preview page")
    p.set_defaults(func=cmd_ui)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
