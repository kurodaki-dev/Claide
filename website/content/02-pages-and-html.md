# Pages & HTML

## HTML tags are functions

Every common HTML tag can be imported from `claide`. Children are positional arguments, attributes are keyword arguments.

```python
from claide import *

div(
    h1("Title", class_="big"),            # class_  -> class
    a("Link", href="/x", data_id=3),      # data_id -> data-id
    input_(type="checkbox", checked=True),
    ul([li(x) for x in ["a", "b"]]),      # lists are flattened
    raw("<b>raw HTML</b>"),               # not escaped
    style={"padding": "1rem"},            # dict -> CSS
)
```

A few tags end with `_` because their name is also a Python builtin or a common module: `input_`, `time_`, `del_`. Every tag, including custom elements, is also available through `tags`:

```python
from claide import tags as t

t.my_widget(t.i("italic"), t.data("42", value=42))   # <my-widget><i>...</i><data ...>
```

| Python | HTML |
|---|---|
| `class_="x"` | `class="x"` |
| `for_="email"` | `for="email"` |
| `data_user_id=1` | `data-user-id="1"` |
| `hidden=True` | `hidden` |
| `hidden=False` or `None` | *(attribute removed)* |
| `t.my_widget()` | `<my-widget></my-widget>` |

> Text is **escaped automatically** to protect you against XSS. Use `raw()` only for HTML you trust.

Elements can be modified after creation:

```python
card = div(class_="card")
card.add(h2("Title"), p("Text"))       # append children
card.add_class("highlight")            # append a CSS class
card.set(id="main")                    # set attributes
```

## Writing content in Markdown

`md()` turns Markdown into HTML. Indentation is removed, so it reads well inside a function:

```python
@route("/about")
def about():
    return md("""
        # About

        I make **websites** in Python. See my [projects](/projects).

        - fast
        - simple
    """)
```

Supported: headings, paragraphs, **bold**, *italic*, `code`, links, lists, `>` quotes, code blocks and tables. Text is escaped, so raw HTML in Markdown is shown as text.

## The `Page` object

Returning elements is enough for most pages: Claide wraps them in a page and uses the first `<h1>` as the title. Return a `Page` when you want to set the title, a description or page-specific files yourself.

A `Page` is a complete HTML document: doctype, `<head>`, `<body>`, metadata and assets.

```python
from claide import Page

page = Page(
    "Home",                       # <title>
    h1("Welcome"),                # body content
    description="My website",     # <meta name="description">
    favicon="/static/icon.png",
    lang="en",
)
page.add(p("More content"))
page.meta(property="og:title", content="Home")
html = page.render()              # full HTML string
page.save("index.html")           # or write it to a file
```

## Fragments and reusable pieces

Any Python function can return elements, so components are just functions:

```python
def user_card(name, avatar):
    return div(img(src=avatar, alt=""), strong(name), class_="user")

@route("/team")
def team():
    return h1("Team"), div([user_card(u.name, u.avatar) for u in users])
```

Use `Fragment(...)` to group elements without a wrapping tag.

## Built-in CSS reset

Every `Page` starts with a tiny stylesheet that removes the blue rectangle mobile browsers draw when you tap a link or a button, and the focus ring that appears after a mouse click. Keyboard users still get a visible focus ring. It comes first in the `<head>`, so your own CSS can override it.

```python
Page("Home", base_css=False)   # leave it out
```

## Attaching CSS and JS to an element

An element can carry its own CSS/JS. It is injected once into the page that contains it:

```python
badge = span("New", class_="badge").with_css(".badge{background:gold}")
```

`with_js(code)`, `with_stylesheet(href)` and `with_script(src)` work the same way.
