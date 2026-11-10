"""Exemple de site complet avec Claide.

    python examples/site_complet.py   ->  http://127.0.0.1:8000
"""

from claide import App, Page, UITemplate, abort, redirect, tags as t
from claide.components import (
    Alert, Button, Card, Field, Footer, Form, Grid, Hero, Navbar, Section,
)

app = App(__name__, secret_key="change-moi-en-production")

# Fichiers liés à TOUTES les pages (dans examples/static/)
app.css(app.static("style.css"))
app.js(app.static("script.js"))

# Composants Uiverse.io / cssbuttons.io (téléchargés une fois puis mis en cache).
# Si pas d'Internet, on se rabat sur un bouton intégré à Claide.
try:
    bouton = UITemplate("https://uiverse.io/0x-Sarthak/hungry-penguin-30").scoped()
except Exception:
    bouton = UITemplate.builtin("gradient")

ARTICLES = {
    1: ("Bienvenue", "Premier article du blog, écrit 100 % en Python."),
    2: ("Uiverse", "Des milliers de composants CSS, utilisables en une ligne."),
}


@app.layout
def base(page):
    page.body.children.insert(0, Navbar("Mon Site", [
        ("Accueil", "/"), ("Blog", "/blog"), ("Contact", "/contact"), ("API", "/api/articles"),
    ]))
    page.add(Footer("© 2026 — Fait avec Claide"))


@app.route("/")
def home(request):
    return Page(
        "Accueil",
        Hero(
            "Un site complet en Python",
            "Pages, formulaires, API, sessions et composants Uiverse.",
            bouton.text("Contact Us", "Me contacter").link("/contact"),
            Button("Voir le blog", "/blog", outline=True),
        ),
        Section(
            Grid(*[Card(titre, texte, href=f"/blog/{i}") for i, (titre, texte) in ARTICLES.items()]),
            title="Derniers articles", alt=True,
        ),
        description="Site d'exemple Claide",
    )


@app.get("/blog")
def blog():
    return Page("Blog", Section(
        t.ul([t.li(t.a(titre, href=app.url_for("article", aid=i))) for i, (titre, _) in ARTICLES.items()]),
        title="Blog",
    ))


@app.get("/blog/<int:aid>")
def article(aid):
    if aid not in ARTICLES:
        abort(404)
    titre, texte = ARTICLES[aid]
    return Page(titre, Section(t.p(texte), title=titre))


@app.route("/contact", methods=["GET", "POST"])
def contact(request):
    if request.method == "POST":
        request.session["nom"] = request.form.get("nom", "")
        return redirect("/merci")
    return Page("Contact", Section(
        Form(
            Field("Nom", "nom", required=True),
            Field("Email", "email", type="email"),
            Field("Sujet", "sujet", type="select", options=["Question", "Bug", "Autre"]),
            Field("Message", "message", type="textarea"),
        ),
        title="Contact",
    ))


@app.get("/merci")
def merci(request):
    return Page("Merci", Section(Alert(f"Merci {request.session.get('nom', '')} !", "success")))


# --- API JSON -------------------------------------------------------------
@app.get("/api/articles")
def api_articles():
    return [{"id": i, "titre": titre} for i, (titre, _) in ARTICLES.items()]


@app.post("/api/articles")
def api_create(request):
    data = request.json or {}
    if "titre" not in data:
        abort(400, "Champ 'titre' requis")
    aid = max(ARTICLES) + 1
    ARTICLES[aid] = (data["titre"], data.get("texte", ""))
    return {"id": aid}, 201


@app.errorhandler(404)
def not_found():
    return Page("Introuvable", Section(t.h1("404"), t.p("Cette page n'existe pas."), Button("Accueil", "/")))


if __name__ == "__main__":
    app.run()
