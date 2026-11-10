# Pages & HTML

## Building HTML with `tags`

`tags` creates any HTML element. Children are positional arguments, attributes are keyword arguments.

```python
from claide import tags as t, raw

t.div(
    t.h1("Title", class_="big"),          # class_  -> class
    t.a("Link", href="/x", data_id=3),    # data_id -> data-id
    t.input(type="checkbox", checked=True),
    t.ul([t.li(x) for x in ["a", "b"]]),  # lists are flattened
    raw("<b>raw HTML</b>"),               # not escaped
    style={"padding": "1rem"},            # dict -> CSS
)
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
card = t.div(class_="card")
card.add(t.h2("Title"), t.p("Text"))   # append children
card.add_class("highlight")            # append a CSS class
card.set(id="main")                    # set attributes
```

## The `Page` object

A `Page` is a complete HTML document: doctype, `<head>`, `<body>`, metadata and assets.

```python
from claide import Page

page = Page(
    "Home",                       # <title>
    t.h1("Welcome"),              # body content
    description="My website",     # <meta name="description">
    favicon="/static/icon.png",
    lang="en",
)
page.add(t.p("More content"))
page.meta(property="og:title", content="Home")
html = page.render()              # full HTML string
page.save("index.html")           # or write it to a file
```

## Fragments and reusable pieces

Any Python function can return elements, so components are just functions:

```python
def user_card(name, avatar):
    return t.div(t.img(src=avatar, alt=""), t.strong(name), class_="user")

page.add(t.div([user_card(u.name, u.avatar) for u in users]))
```

Use `Fragment(...)` to group elements without a wrapping tag.

## Attaching CSS and JS to an element

An element can carry its own CSS/JS. It is injected once into the page that contains it:

```python
badge = t.span("New", class_="badge").with_css(".badge{background:gold}")
```

`with_js(code)`, `with_stylesheet(href)` and `with_script(src)` work the same way.
