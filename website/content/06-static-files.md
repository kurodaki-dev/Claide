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

## Linked automatically

If they exist, these files are used on every page without writing anything:

| File | Becomes |
|---|---|
| `static/style.css` | `<link rel="stylesheet">` in the `<head>` |
| `static/script.js` | `<script src>` at the end of the `<body>` |
| `static/favicon.svg`, `.png` or `.ico` | the page icon |

Turn this off with `App(auto_static=False)`.

## Linking other files on every page

```python
app = default_app()          # the app behind @route / run(), or your own App
app.css("https://fonts.googleapis.com/css2?family=Inter&display=swap")
app.css(app.static("print.css"))
app.js(app.static("chart-setup.js"))
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
