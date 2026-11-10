"""Ligne de commande : ``claide new``, ``claide run``, ``claide build``, ``claide ui``."""

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

NAV = Navbar("{name}", [("Accueil", "/"), ("Contact", "/contact")])
bouton = UITemplate.builtin("gradient", "Commencer")


@app.layout
def base(page):
    page.body.children.insert(0, NAV)
    page.add(Footer("Fait avec Claide 🐍"))


@app.route("/")
def home(request):
    visites = request.session.get("visites", 0) + 1
    request.session["visites"] = visites
    return Page(
        "{name}",
        Hero("Bienvenue sur {name}", f"Tu es venu {{visites}} fois.", bouton.link("/contact")),
        Section(
            Grid(
                Card("Rapide", "100 % Python, zéro dépendance."),
                Card("Complet", "Routes, formulaires, API, sessions."),
                Card("Joli", "Composants Uiverse.io intégrés."),
            ),
            title="Pourquoi Claide ?",
        ),
    )


@app.route("/contact", methods=["GET", "POST"])
def contact(request):
    message = None
    if request.method == "POST":
        message = Alert(f"Merci {{request.form.get('nom', '')}} !", "success")
    return Page("Contact", Section(
        message,
        Form(Field("Nom", "nom", required=True), Field("Message", "message", type="textarea")),
        title="Contact",
    ))


@app.get("/api/hello/<name>")
def api_hello(name):
    return {{"message": f"Salut {{name}} !"}}


if __name__ == "__main__":
    app.run()
'''

CSS_TEMPLATE = """/* Ton CSS ici */
:root { --cl-primary: #6366f1; }
"""

JS_TEMPLATE = """// Ton JavaScript ici
console.log("Claide est prêt ✦");
"""


def _load_app(target: str):
    """'app:app' ou 'app.py' -> objet App."""
    sys.path.insert(0, os.getcwd())
    module_name, _, attr = target.partition(":")
    if module_name.endswith(".py"):
        module_name = module_name[:-3].replace(os.sep, ".").replace("/", ".")
    module = importlib.import_module(module_name)
    app = getattr(module, attr or "app", None)
    if app is None:
        raise SystemExit(f"Aucun objet '{attr or 'app'}' dans {module_name}")
    return app


def cmd_new(args: argparse.Namespace) -> None:
    import secrets

    root = args.name
    if os.path.exists(root) and os.listdir(root):
        raise SystemExit(f"Le dossier '{root}' existe déjà et n'est pas vide.")
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
    print(f"✦ Projet créé dans {root}/\n\n  cd {root}\n  python app.py\n")


def cmd_run(args: argparse.Namespace) -> None:
    app = _load_app(args.app)
    app.debug = not args.prod
    from .server import run_server

    run_server(app, args.host, args.port, reload=False)


def cmd_build(args: argparse.Namespace) -> None:
    app = _load_app(args.app)
    written = app.build(args.out)
    print(f"✦ {len(written)} page(s) générée(s) dans {args.out}/")


def cmd_ui(args: argparse.Namespace) -> None:
    from .uitemplate import UITemplate

    tpl = UITemplate(args.ref, category=args.category)
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(tpl.html + "\n\n<style>\n" + tpl.css + "\n</style>\n")
            if tpl.js:
                f.write("\n<script>\n" + tpl.js + "\n</script>\n")
        print(f"✦ Sauvegardé dans {args.save}")
    elif args.preview:
        print(f"✦ Aperçu : {tpl.preview()}")
    else:
        print(f"<!-- {tpl!r} -->\n{tpl.html}\n\n<style>\n{tpl.css}\n</style>")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(prog="claide", description="Crée des sites web en Python.")
    parser.add_argument("--version", action="version", version=f"claide {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="Crée un nouveau projet")
    p.add_argument("name")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("run", help="Lance une app (ex. claide run app:app)")
    p.add_argument("app", nargs="?", default="app:app")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--prod", action="store_true", help="Désactive le mode debug")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("build", help="Exporte les pages en HTML statique")
    p.add_argument("app", nargs="?", default="app:app")
    p.add_argument("--out", default="dist")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("ui", help="Télécharge un composant Uiverse (auteur/nom ou URL)")
    p.add_argument("ref")
    p.add_argument("--category", default=None)
    p.add_argument("--save", default=None, help="Fichier .html de sortie")
    p.add_argument("--preview", action="store_true", help="Génère une page d'aperçu")
    p.set_defaults(func=cmd_ui)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
