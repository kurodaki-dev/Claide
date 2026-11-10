# CSS, JS & static files

## The `static` folder

Every file in the `static/` folder next to your app is served under `/static/`:

```text
mysite/
├── app.py
└── static/
    ├── style.css
    ├── script.js
    └── img/logo.png
```

`app.static("img/logo.png")` returns the right URL (`/static/img/logo.png`, including the [base path](/docs/deployment) if there is one).

## Linking CSS and JS on every page

```python
app = App(__name__)
app.css(app.static("style.css"))
app.js(app.static("script.js"))
app.css("https://fonts.googleapis.com/css2?family=Inter&display=swap")
```

## On a single page

```python
page = Page("Dashboard")
page.css(app.static("dashboard.css"))
page.js("https://cdn.jsdelivr.net/npm/chart.js")
```

## Inline CSS and JS

```python
page.style("h1 { color: crimson; }")
page.script("console.log('hello')")
page.style_file("theme.css")      # inline the content of a local file
page.script_file("widget.js")
```

| Method | Output | Position |
|---|---|---|
| `css(href)` | `<link rel="stylesheet">` | `<head>` |
| `style(css)` | `<style>` | `<head>` |
| `js(src)` | `<script src>` | end of `<body>` |
| `script(code)` | `<script>` | end of `<body>` |

Assets are **deduplicated**: linking the same file twice outputs it once.

## Custom folder

```python
app = App(__name__, static_folder="assets", static_url="/assets")
app = App(__name__, static_folder=None)    # disable static files
```
