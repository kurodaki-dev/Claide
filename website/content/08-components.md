# Layout components

## The default theme

Sites written with `@route` / `run()` use a built-in **classless theme**: plain HTML (headings, text, links, forms, buttons, tables, code) looks clean without a single CSS class, in light and dark mode. Enable it on your own app with `App(theme=True)`. It only styles bare elements with low priority, so your `static/style.css` overrides it easily.

## Ready-made blocks

`claide.components` provides ready-made building blocks with a clean default style. Their CSS is included automatically.

```python
from claide.components import (
    Navbar, Hero, Section, Grid, Card, Button, Alert, Form, Field, Footer, Container,
)
```

## A full page in a few lines

```python
Page("Home",
    Navbar("My site", [("Home", "/"), ("Blog", "/blog"), ("Contact", "/contact")], current="/"),
    Hero("Welcome", "A short subtitle", Button("Get started", "/start"), Button("Docs", "/docs", outline=True)),
    Section(
        Grid(
            Card("Fast", "Pure Python."),
            Card("Pretty", "Uiverse components.", image="/static/pretty.jpg", href="/pretty"),
        ),
        title="Features", alt=True,
    ),
    Footer("© 2026 My site"),
)
```

## Reference

| Component | Signature |
|---|---|
| `Navbar` | `Navbar(brand, links=[(label, href)], current=None)` |
| `Hero` | `Hero(title, subtitle=None, *actions)` |
| `Section` | `Section(*children, title=None, alt=False, id=None)` |
| `Grid` | `Grid(*children, min_width="250px")` (responsive columns) |
| `Card` | `Card(title, *texts, image=None, href=None)` |
| `Button` | `Button(label, href=None, outline=False)` (a link if `href` is set) |
| `Alert` | `Alert(message, kind="info")` (`info`, `success`, `error`) |
| `Form` | `Form(*fields, action="", method="post", submit="Submit", upload=False)` |
| `Field` | `Field(label, name, type="text", value=None, required=False, options=None)` |
| `Footer` | `Footer(*children)` |
| `Container` | `Container(*children)` (centered, max 1100px) |

Every component accepts extra HTML attributes as keyword arguments (`id=`, `class_=`, `style=`...).

## Theming

The components use CSS variables. Override them in your own stylesheet:

```css
:root {
  --cl-primary: #7c3aed;
  --cl-text: #111827;
  --cl-muted: #6b7280;
  --cl-bg: #ffffff;
  --cl-surface: #f9fafb;
  --cl-border: #e5e7eb;
  --cl-radius: 12px;
}
```
