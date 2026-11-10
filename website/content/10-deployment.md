# Deployment

## Development server

`app.run()` starts a multi-threaded server with automatic reload:

```python
app.run(host="127.0.0.1", port=8000, debug=True)
```

> The development server is not meant for production traffic. Use a WSGI server instead.

## Production (WSGI)

`App` is a standard WSGI application, so it works with any WSGI server:

```bash
pip install gunicorn
gunicorn app:app --workers 4 --bind 0.0.0.0:8000
```

On Windows, use `waitress`:

```bash
pip install waitress
waitress-serve --port=8000 app:app
```

This also works on platforms like Render, Railway, Fly.io or PythonAnywhere: point them at `app:app`.

## Static export

Sites without server logic can be exported as plain HTML files and hosted anywhere (GitHub Pages, Netlify, Cloudflare Pages...):

```python
app.build("dist")                                    # or: claide build app:app
app.build("dist", extra_paths=["/blog/1", "/blog/2"]) # also export dynamic routes
```

Every `GET` route without parameters is exported: `/` becomes `index.html`, `/about` becomes `about/index.html`, and the `static/` folder is copied. If you defined `@app.errorhandler(404)`, a `404.html` is generated too.

## Serving under a sub-path

GitHub Pages project sites live under `https://user.github.io/RepoName/`. Tell Claide with `base_path`, and build URLs with `app.url()`, `app.static()` and `app.url_for()`:

```python
import os

app = App(__name__, base_path=os.environ.get("BASE_PATH", ""))

Navbar("My site", [("Home", app.url("/")), ("Docs", app.url("/docs"))])
app.css(app.static("style.css"))
```

## GitHub Pages with GitHub Actions

This documentation is itself a Claide app deployed this way. Create `.github/workflows/pages.yml`:

```yaml
name: Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install claide-web
      - run: python -c "from app import app; app.build('_site')"
        env:
          BASE_PATH: /${{ github.event.repository.name }}
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site
      - id: deployment
        uses: actions/deploy-pages@v4
```

Then in your repository: **Settings → Pages → Source: GitHub Actions**.
