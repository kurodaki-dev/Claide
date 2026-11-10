# Getting started

Claide is a Python module to build complete websites, from the HTML to the server, with **zero dependencies**. You write pages in Python, link your own `style.css` / `script.js`, and drop in ready-made components from [Uiverse.io](https://uiverse.io) / [cssbuttons.io](https://cssbuttons.io).

## Installation

```bash
pip install claide-web
```

The package is called `claide-web` on PyPI, but you import it as `claide`. Python 3.9 or newer is required.

## Your first site

```python
from claide import App, Page, tags as t

app = App(__name__)

@app.route("/")
def home():
    return Page("Home", t.h1("Hello!"), t.p("My first Claide website."))

if __name__ == "__main__":
    app.run()
```

Run it with `python app.py` and open [http://127.0.0.1:8000](http://127.0.0.1:8000). The development server **reloads automatically** when you save a `.py`, `.css`, `.js` or `.html` file.

## Start from a template

The `claide new` command creates a ready-to-run project with a navbar, a contact form, a JSON route, sessions and linked CSS/JS files:

```bash
claide new mysite
cd mysite
python app.py
```

```text
mysite/
├── app.py
└── static/
    ├── style.css
    └── script.js
```

## What's next?

- [Pages & HTML](/docs/pages-and-html): build HTML with Python.
- [Routing & requests](/docs/routing): URLs, parameters, forms, JSON.
- [Uiverse components](/docs/uiverse): use thousands of CSS components in one line.
- [Deployment](/docs/deployment): put your site online.
