# Claide ✦

**Build complete websites in Python, from A to Z**: HTML pages, dynamic routes,
forms, file uploads, JSON APIs, sessions, your own `style.css` / `script.js`, and
the thousands of components from [cssbuttons.io](https://cssbuttons.io) / [Uiverse.io](https://uiverse.io)
in a single line. Zero dependencies.

```bash
pip install claide-web
```

The package is published on PyPI as `claide-web`, but you import it as `claide`.

📖 **Documentation: https://kurodaki-dev.github.io/Claide/**, a website built with Claide itself (see [`website/`](website/)).

## Quick start

```python
from claide import *

@route("/")
def home():
    return h1("Hello!"), p("Welcome to my site.")

run()
```

`python app.py`, open http://127.0.0.1:8000, done. The page has a clean default style,
its title comes from the `<h1>`, and the server reloads when you save.

```python
@route("/contact")
def contact(name: str = "", age: int = 0):      # form fields arrive as parameters
    if request.method == "POST":
        request.session["name"] = name            # sessions work without any setup
        return h1(f"Thanks {name}!")
    return h1("Contact"), form(
        label("Name", input_(name="name")),
        label("Age", input_(name="age", type="number")),
        button("Send"),
        method="post",
    )

@get("/api/square/<int:n>")
def square(n):
    return {"square": n * n}                      # a dict is sent as JSON
```

- Every HTML tag is a function: `h1`, `p`, `div`, `a`, `img`, `form`, `input_`...
- `static/style.css`, `static/script.js` and `static/favicon.*` are linked automatically.
- `md("""...""")` turns Markdown into HTML; `ui("https://uiverse.io/...")` adds a Uiverse component.

Or start from a template:

```bash
claide new mysite
cd mysite
python app.py
```

## Uiverse / cssbuttons.io components

Copy the URL of an element on uiverse.io (cssbuttons.io redirects to uiverse.io/buttons):

```python
from claide import UITemplate          # or: from claide import uitemplate

button = UITemplate("https://uiverse.io/0x-Sarthak/hungry-penguin-30")
# or UITemplate("0x-Sarthak/hungry-penguin-30")

page.add(
    button
      .text("Contact Us", "Write me")     # change the text
      .attrs(id="send", onclick="go()")   # add attributes
      .link("/contact")                   # turn it into a link
)
```

- The component's CSS is **injected automatically** into the `<head>` (only once).
- Tailwind-based components load Tailwind by themselves.
- `.scoped()` isolates the component's CSS (selectors are prefixed and `@keyframes`
  renamed), so rules like `button { ... }` don't leak onto the rest of your page and two
  components that both use `.button` don't conflict. `.prefix("x-")` renames classes instead.
- `.add_css("...")` lets you override colors.
- `UITemplate(html="...", css="...")` or `UITemplate.from_file("button.html")` for your own code.
- `UITemplate.builtin("glow", "Send")`: bundled components that work offline
  (`gradient`, `glow`, `slide`, `pushable`, `spinner`, `toggle`, `card`).
- Components are downloaded from the official `uiverse-io/galaxy` repository
  (MIT license) and cached in `~/.cache/claide`.

From the command line: `claide ui author/name --preview` or `--save button.html`.

## Linking your CSS / JS files

```
mysite/
├── app.py
└── static/
    ├── style.css
    ├── script.js
    └── logo.png
```

```python
app.css(app.static("style.css"))   # on every page
app.js(app.static("script.js"))

page = Page("Contact")
page.css("/static/contact.css")    # on a single page
page.js("https://cdn.jsdelivr.net/npm/chart.js")
page.style("h1 { color: red }")    # inline CSS
page.script("console.log('hi')")   # inline JS
page.style_file("theme.css")       # inline the content of a file
```

## Building HTML in Python

```python
from claide import tags as t, raw

t.div(
    t.h1("Title", class_="big"),          # class_ -> class
    t.a("Link", href="/x", data_id=3),    # data_id -> data-id
    t.input(type="checkbox", checked=True),
    t.ul([t.li(x) for x in ["a", "b"]]),
    raw("<b>raw HTML</b>"),
    style={"padding": "1rem"},
)
```

Text is escaped automatically (XSS protection) except with `raw()`.

Every `Page` also includes a tiny CSS reset that removes the blue tap highlight on mobile
(disable it with `Page(..., base_css=False)`).

### Layout components

```python
from claide.components import Navbar, Hero, Section, Grid, Card, Footer, Form, Field, Button, Alert

Page("Home",
    Navbar("My site", [("Home", "/"), ("Contact", "/contact")]),
    Hero("Welcome", "Subtitle", Button("Get started", "/start")),
    Section(Grid(Card("A", "text"), Card("B", "text", image="/static/b.jpg")), title="Services"),
    Footer("© 2026"),
)
```

## Dynamic server

```python
from claide import App, Page, Router, redirect, abort, send_file

app = App(__name__, secret_key="change-me")

@app.get("/user/<int:uid>")              # converters: str, int, float, slug, path
def user(uid, request):
    page = request.args.get("page", "1") # ?page=2
    return Page(f"User {uid}", ...)

@app.route("/contact", methods=["GET", "POST"])
def contact(request):
    if request.method == "POST":
        name = request.form["name"]
        request.files["cv"].save("uploads/")    # file upload
        request.session["name"] = name          # session (signed cookie)
        return redirect("/thanks")
    return Page(...)

@app.post("/api/items")
def create(request):
    data = request.json
    return {"ok": True, "item": data}, 201   # dict/list -> JSON

@app.errorhandler(404)
def not_found():
    return Page("Oops", t.h1("Page not found"))

@app.layout                                  # applied to every Page
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

A route can return: a `Page`, an element, a `UITemplate`, `str`, `dict`/`list` (JSON),
a `Response`, a generator (streaming), or a `(body, status, headers)` tuple.

### Production

`App` is a standard **WSGI** application:

```bash
pip install gunicorn
gunicorn app:app
```

### Static export (optional)

```bash
claide build app:app --out dist     # or app.build("dist")
```

Serving under a sub-path (e.g. a GitHub Pages project site)? Use `App(base_path="/RepoName")`
and build links with `app.url("/page")`, `app.static(...)` and `app.url_for(...)`.

## Testing

```python
client = app.test_client()
assert client.get("/").status == 200
assert client.post("/api/items", json_data={"a": 1}).json["ok"]
```

## Automatic PyPI publishing

`.github/workflows/ci.yml` runs the tests, builds the package, then publishes it
to PyPI on every push to `main` (and on `v*` tags). If the version already exists,
nothing is uploaded: **bump `__version__` in `claide/__init__.py` to release.**

One-time setup:

1. On [pypi.org](https://pypi.org/manage/account/token/), create an API token.
2. On GitHub: *Settings → Secrets and variables → Actions → New repository secret*,
   name **`PYPI_API_TOKEN`**, value = the token (`pypi-...`).
3. The job uses the `pypi` GitHub environment (created automatically; you can add
   a manual approval in *Settings → Environments*).

## License

MIT. Uiverse.io components are MIT licensed; please credit their authors
(Claide automatically adds a credit comment in the CSS).
