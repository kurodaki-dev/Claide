# Responses

## What a route can return

| Return value | Result |
|---|---|
| `Page(...)` | full HTML page |
| an element, a `UITemplate` | wrapped in a page automatically |
| `str` / `bytes` | sent as HTML |
| `dict` / `list` | JSON (`application/json`) |
| `None` | `204 No Content` |
| a generator | streamed response |
| `Response(...)` | sent as is |
| `(body, status)` or `(body, status, headers)` | custom status and headers |

```python
@app.post("/api/items")
def create(request):
    return {"id": 42}, 201
```

## Redirects and errors

```python
from claide import redirect, abort

@app.get("/old")
def old():
    return redirect("/new")          # 302 by default

@app.get("/admin")
def admin(request):
    if not request.session.get("admin"):
        abort(403)                   # or: raise HTTPError(403, "message")
```

Customize error pages with `errorhandler`:

```python
@app.errorhandler(404)
def not_found():
    return Page("Not found", t.h1("This page does not exist"))
```

Errors on paths starting with `/api` (or requests that accept JSON) are returned as JSON automatically. In debug mode, uncaught exceptions show a traceback page.

## The `Response` class

```python
from claide import Response

resp = Response("hello", status=200, content_type="text/plain; charset=utf-8")
resp.set_header("Cache-Control", "no-store")
resp.set_cookie("theme", "dark", max_age=3600)
resp.delete_cookie("old")
```

## Files and streaming

```python
from claide import send_file

@app.get("/report")
def report():
    return send_file("report.pdf", as_attachment=True)

@app.get("/events")
def events():
    def gen():
        for i in range(10):
            yield f"data: {i}\n\n"
    return Response(gen(), content_type="text/event-stream")
```

## Shared layout

`@app.layout` runs on every `Page` before it is rendered. Use it for navbars, footers or global metadata:

```python
@app.layout
def base(page):
    page.body.children.insert(0, navbar)
    page.add(footer)
```
