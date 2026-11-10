# Claide ✦

**Crée des sites web complets en Python, de A à Z** : pages HTML, routes dynamiques,
formulaires, uploads, API JSON, sessions, fichiers `style.css` / `script.js`, et
les milliers de composants de [cssbuttons.io](https://cssbuttons.io) / [Uiverse.io](https://uiverse.io)
en une ligne. Zéro dépendance.

```bash
pip install claide
```

## Démarrage rapide

```bash
claide new monsite
cd monsite
python app.py        # -> http://127.0.0.1:8000 (rechargement automatique)
```

```python
from claide import App, Page, tags as t

app = App(__name__)

@app.route("/")
def home():
    return Page("Accueil", t.h1("Salut !"), t.p("Mon premier site Claide."))

app.run()
```

## Composants Uiverse / cssbuttons.io

Copie l'URL d'un élément sur uiverse.io (cssbuttons.io redirige vers uiverse.io/buttons) :

```python
from claide import UITemplate          # ou : from claide import uitemplate

bouton = UITemplate("https://uiverse.io/0x-Sarthak/hungry-penguin-30")
# ou UITemplate("0x-Sarthak/hungry-penguin-30")

page.add(
    bouton
      .text("Contact Us", "Écris-moi")     # change le texte
      .attrs(id="envoyer", onclick="go()") # ajoute des attributs
      .link("/contact")                    # en fait un lien
)
```

- Le CSS du composant est **injecté automatiquement** dans le `<head>` (une seule fois).
- Les composants écrits en Tailwind chargent Tailwind tout seuls.
- `.scoped()` / `.prefix("x-")` renomment les classes pour éviter les conflits
  (ex. deux composants qui utilisent `.button`).
- `.add_css("...")` pour surcharger des couleurs.
- `UITemplate(html="...", css="...")` ou `UITemplate.from_file("bouton.html")` pour ton propre code.
- `UITemplate.builtin("glow", "Envoyer")` : composants intégrés, sans Internet
  (`gradient`, `glow`, `slide`, `pushable`, `spinner`, `toggle`, `card`).
- Les composants sont téléchargés depuis le dépôt officiel `uiverse-io/galaxy`
  (licence MIT) puis mis en cache dans `~/.cache/claide`.

En ligne de commande : `claide ui auteur/nom --preview` ou `--save bouton.html`.

## Lier ses fichiers CSS / JS

```
monsite/
├── app.py
└── static/
    ├── style.css
    ├── script.js
    └── logo.png
```

```python
app.css(app.static("style.css"))   # sur toutes les pages
app.js(app.static("script.js"))

page = Page("Contact")
page.css("/static/contact.css")    # sur une seule page
page.js("https://cdn.jsdelivr.net/npm/chart.js")
page.style("h1 { color: red }")    # CSS inline
page.script("console.log('hi')")   # JS inline
page.style_file("theme.css")       # intègre le contenu d'un fichier
```

## Construire le HTML en Python

```python
from claide import tags as t, raw

t.div(
    t.h1("Titre", class_="big"),          # class_ -> class
    t.a("Lien", href="/x", data_id=3),    # data_id -> data-id
    t.input(type="checkbox", checked=True),
    t.ul([t.li(x) for x in ["a", "b"]]),
    raw("<b>HTML brut</b>"),
    style={"padding": "1rem"},
)
```

Le texte est échappé automatiquement (protection XSS) sauf avec `raw()`.

### Composants de mise en page

```python
from claide.components import Navbar, Hero, Section, Grid, Card, Footer, Form, Field, Button, Alert

Page("Accueil",
    Navbar("Mon site", [("Accueil", "/"), ("Contact", "/contact")]),
    Hero("Bienvenue", "Sous-titre", Button("Commencer", "/start")),
    Section(Grid(Card("A", "texte"), Card("B", "texte", image="/static/b.jpg")), title="Services"),
    Footer("© 2026"),
)
```

## Serveur dynamique

```python
from claide import App, Page, Router, redirect, abort, send_file

app = App(__name__, secret_key="change-moi")

@app.get("/user/<int:uid>")              # convertisseurs : str, int, float, slug, path
def user(uid, request):
    page = request.args.get("page", "1") # ?page=2
    return Page(f"User {uid}", ...)

@app.route("/contact", methods=["GET", "POST"])
def contact(request):
    if request.method == "POST":
        nom = request.form["nom"]
        request.files["cv"].save("uploads/")   # upload
        request.session["nom"] = nom            # session (cookie signé)
        return redirect("/merci")
    return Page(...)

@app.post("/api/items")
def create(request):
    data = request.json
    return {"ok": True, "item": data}, 201   # dict/list -> JSON

@app.errorhandler(404)
def not_found():
    return Page("Oups", t.h1("Page introuvable"))

@app.layout                                  # appliqué à chaque Page
def base(page):
    page.body.children.insert(0, navbar)

@app.before_request
def auth(request):
    if request.path.startswith("/admin") and not request.session.get("admin"):
        return redirect("/login")

api = Router("/api/v2")
@api.get("/ping")
def ping(): return {"pong": True}
app.include(api)
```

Une route peut renvoyer : `Page`, un élément, un `UITemplate`, `str`, `dict`/`list` (JSON),
`Response`, un générateur (streaming), ou un tuple `(contenu, statut, en-têtes)`.

### Production

`App` est une application **WSGI** standard :

```bash
pip install gunicorn
gunicorn app:app
```

### Export statique (optionnel)

```bash
claide build app:app --out dist     # ou app.build("dist")
```

## Tests

```python
client = app.test_client()
assert client.get("/").status == 200
assert client.post("/api/items", json_data={"a": 1}).json["ok"]
```

## Publication automatique sur PyPI

Le workflow `.github/workflows/ci.yml` lance les tests puis publie sur PyPI à
chaque push sur `main` (et sur les tags `v*`). Si la version existe déjà, rien
n'est envoyé : **augmente `__version__` dans `claide/__init__.py` pour publier.**

À configurer une seule fois :

1. Sur [pypi.org](https://pypi.org/manage/account/token/), crée un token API.
2. Sur GitHub : *Settings → Secrets and variables → Actions → New repository secret*,
   nom **`PYPI_API_TOKEN`**, valeur = le token (`pypi-...`).
3. Le job utilise l'environnement GitHub `pypi` (créé automatiquement ; tu peux y
   ajouter une validation manuelle dans *Settings → Environments*).

## Licence

MIT. Les composants Uiverse.io sont sous licence MIT ; pense à créditer leurs auteurs
(Claide ajoute automatiquement un commentaire de crédit dans le CSS).
