# Routing & requests

## Routes

```python
from claide import App

app = App(__name__)

@app.route("/")                          # GET by default
def home(): ...

@app.route("/contact", methods=["GET", "POST"])
def contact(request): ...

@app.get("/items")
@app.post("/items")                      # also: put, patch, delete
def items(request): ...
```

## URL parameters

```python
@app.get("/user/<int:uid>")
def user(uid):
    return f"User {uid}"

@app.get("/files/<path:filepath>")
def files(filepath): ...
```

| Converter | Matches | Python type |
|---|---|---|
| `<name>` / `<str:name>` | anything but `/` | `str` |
| `<int:name>` | `42`, `-3` | `int` |
| `<float:name>` | `1.5` | `float` |
| `<slug:name>` | letters, digits, `-`, `_` | `str` |
| `<path:name>` | anything, including `/` | `str` |

Build URLs from function names with `app.url_for("user", uid=3)` → `/user/3`. Extra arguments become the query string.

## The request object

Add a `request` parameter to your function to receive it. URL parameters are passed by name.

```python
@app.post("/search/<category>")
def search(category, request):
    request.method        # "POST"
    request.path          # "/search/books"
    request.args["q"]     # query string  ?q=...
    request.form["name"]  # form field
    request.json          # decoded JSON body
    request.files["cv"]   # uploaded file
    request.cookies       # dict of cookies
    request.headers       # dict of headers
    request.session       # signed session (see Sessions)
    request.get("q")      # looks in params, form, JSON then query string
```

For fields sent several times (checkboxes, multi-selects), use `request.form.getlist("tags")`.

## Routers

Group routes and mount them with a prefix:

```python
from claide import Router

api = Router("/api")

@api.get("/users")
def users():
    return [{"id": 1, "name": "Ann"}]

app.include(api)            # -> GET /api/users
```

## Hooks

```python
@app.before_request
def require_login(request):
    if request.path.startswith("/admin") and not request.session.get("user"):
        return redirect("/login")      # returning a value stops the request

@app.after_request
def add_header(request, response):
    response.set_header("X-Frame-Options", "DENY")
    return response
```
