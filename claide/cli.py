"""Command line: ``claide new``, ``claide run``, ``claide build``, ``claide ui``."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from typing import List, Optional

from . import __version__

APP_TEMPLATE = '''from claide import *


@layout
def base(page):
    page.body.children.insert(0, nav(ul(li(a("Home", href="/")), li(a("Contact", href="/contact")))))


@route("/")
def home():
    visits = request.session.get("visits", 0) + 1
    request.session["visits"] = visits
    return (
        h1("Welcome to {name}"),
        p(f"You have been here {{visits}} time(s)."),
        md("""
            Edit **app.py** and save: the page reloads by itself.
            Your CSS goes in **static/style.css**, your JavaScript in **static/script.js**.
        """),
        ui.builtin("gradient", "Contact me").link("/contact"),
    )


@route("/contact")
def contact(name: str = "", message: str = ""):
    if request.method == "POST":
        return h1(f"Thanks {{name}}!"), p("Your message was received.")
    return h1("Contact"), form(
        label("Name", input_(name="name", required=True)),
        label("Message", textarea(name="message", rows=5)),
        button("Send"),
        method="post",
    )


@get("/api/hello/<name>")
def api_hello(name):
    return {{"message": f"Hello {{name}}!"}}


run()
'''

CSS_TEMPLATE = """/* Your CSS here. It is linked on every page automatically. */
"""

JS_TEMPLATE = """// Your JavaScript here. It is loaded on every page automatically.
console.log("Claide is ready");
"""


def _load_app(target: str):
    """'app:app' or 'app.py' -> App object."""
    sys.path.insert(0, os.getcwd())
    module_name, _, attr = target.partition(":")
    if module_name.endswith(".py"):
        module_name = module_name[:-3].replace(os.sep, ".").replace("/", ".")
    module = importlib.import_module(module_name)
    app = getattr(module, attr or "app", None)
    if app is None and not attr:
        from . import quick

        app = quick._app  # site written with @route / run() shortcuts
    if app is None:
        raise SystemExit(f"No object '{attr or 'app'}' in {module_name}")
    return app


def cmd_new(args: argparse.Namespace) -> None:
    root = args.name
    if os.path.exists(root) and os.listdir(root):
        raise SystemExit(f"The folder '{root}' already exists and is not empty.")
    os.makedirs(os.path.join(root, "static"), exist_ok=True)
    name = os.path.basename(os.path.abspath(root))
    files = {
        "app.py": APP_TEMPLATE.format(name=name),
        os.path.join("static", "style.css"): CSS_TEMPLATE,
        os.path.join("static", "script.js"): JS_TEMPLATE,
    }
    for rel, content in files.items():
        with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"Project created in {root}/\n\n  cd {root}\n  python app.py\n")


def cmd_run(args: argparse.Namespace) -> None:
    app = _load_app(args.app)
    app.debug = not args.prod
    from .server import run_server

    run_server(app, args.host, args.port, reload=False)


def cmd_build(args: argparse.Namespace) -> None:
    app = _load_app(args.app)
    written = app.build(args.out)
    print(f"{len(written)} page(s) written to {args.out}/")


def cmd_ui(args: argparse.Namespace) -> None:
    from .uitemplate import TEMPLATES_FOLDER, UITemplate

    folder = args.folder or os.path.join(os.getcwd(), TEMPLATES_FOLDER)
    tpl = UITemplate(args.ref, category=args.category, folder=folder)
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(tpl.html + "\n\n<style>\n" + tpl.css + "\n</style>\n")
            if tpl.js:
                f.write("\n<script>\n" + tpl.js + "\n</script>\n")
        print(f"Saved to {args.save}")
    if tpl.path:
        print(f"Component saved in {os.path.relpath(tpl.path)}")
        print(f'Use it with: ui("{tpl.author}/{tpl.name}")')
    if args.preview:
        print(f"Preview: {tpl.preview()}")


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

    p = sub.add_parser("ui", help="Download a Uiverse component into ./templates (author/name or URL)")
    p.add_argument("ref")
    p.add_argument("--category", default=None)
    p.add_argument("--save", default=None, help="Also write the component to this .html file")
    p.add_argument("--folder", default=None, help="Templates folder (default: ./templates)")
    p.add_argument("--preview", action="store_true", help="Generate a preview page")
    p.set_defaults(func=cmd_ui)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
