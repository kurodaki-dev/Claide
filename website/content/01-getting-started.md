# Getting started

Claide is a Python module to build complete websites, from the HTML to the server, with **zero dependencies**. You write pages in Python, put your CSS and JavaScript in a `static` folder, and drop in ready-made components from [Uiverse.io](https://uiverse.io) / [cssbuttons.io](https://cssbuttons.io).

## Installation

```bash
pip install claide-web
```

The package is called `claide-web` on PyPI, but you import it as `claide`. Python 3.9 or newer is required.

## A website in five lines

Create `app.py`:

```python
from claide import *

@route("/")
def home():
    return h1("Hello!"), p("Welcome to my site.")

run()
```

Run `python app.py` and open [http://127.0.0.1:8000](http://127.0.0.1:8000). That's a complete website:

- every HTML tag is a function: `h1`, `p`, `div`, `a`, `img`, `button`, `form`...
- return one or several elements and Claide makes the page around them, with the `<h1>` as the title;
- the page has a clean default style, so you don't need any CSS to start;
- the server **reloads by itself** when you save a file.

## Adding pages, forms and data

```python
from claide import *

@route("/")
def home():
    return (
        h1("My site"),
        p("Hello! ", a("Write to me", href="/contact")),
    )

@route("/contact")
def contact(name: str = "", message: str = ""):
    if request.method == "POST":
        return h1(f"Thanks {name}!")
    return h1("Contact"), form(
        label("Name", input_(name="name")),
        label("Message", textarea(name="message")),
        button("Send"),
        method="post",
    )

@get("/api/time")
def api_time():
    import datetime
    return {"now": datetime.datetime.now().isoformat()}   # a dict is sent as JSON

run()
```

Things to notice:

- **Form fields arrive as parameters.** `name` and `message` are filled from the form, the URL (`?name=...`) or a JSON body. Add a type (`age: int`, `news: bool`) and Claide converts the value for you.
- `request` is always available: `request.method`, `request.args`, `request.session`...
- `@route` accepts GET and POST. Use `@get` or `@post` to accept only one.

## Your CSS and JavaScript

Put them in a `static` folder next to `app.py`:

```text
mysite/
├── app.py
└── static/
    ├── style.css      <- linked on every page automatically
    ├── script.js      <- loaded on every page automatically
    └── favicon.png    <- used as the icon automatically
```

There is nothing to write in Python: Claide finds these files by itself. Other files in `static/` are served at `/static/...` (for example `img(src="/static/photo.jpg")`).

## Start from a template

```bash
claide new mysite
cd mysite
python app.py
```

`claide new` creates a small project with a navigation bar, a contact form, a JSON route, a session counter and the `static` folder.

## Two ways to write a Claide site

The shortcuts above (`route`, `run`) are all most sites need. When you want more control (several apps, a custom static folder, a sub-path...), create the application yourself. Everything else works the same:

```python
from claide import App, h1

app = App(__name__, theme=True)

@app.route("/")
def home():
    return h1("Hello!")

app.run()
```

## What's next?

- [Pages & HTML](/docs/pages-and-html): tags, pages, Markdown.
- [Routing & requests](/docs/routing): URLs, parameters, forms, JSON.
- [Uiverse components](/docs/uiverse): thousands of CSS components in one line.
- [Deployment](/docs/deployment): put your site online.
