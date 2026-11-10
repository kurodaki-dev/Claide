# Routing & requests

## Routes

```python
from claide import *

@route("/")                  # GET and POST
def home(): ...

@get("/items")               # GET only
def items(): ...

@post("/items")              # POST only (also: put, delete)
def add_item(): ...

run()
```

With an `App` object, use `@app.route(path, methods=[...])`, `@app.get`, `@app.post`, `@app.put`, `@app.patch` and `@app.delete`. `@app.route` accepts only GET unless you list other methods.

## URL parameters

```python
@get("/user/<int:uid>")
def user(uid):
    return h1(f"User {uid}")

@get("/files/<path:filepath>")
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

## Form and query values as parameters

Any parameter that is not part of the URL is looked up in the form, the JSON body, then the query string:

```python
@route("/signup")
def signup(email: str, age: int = 18, newsletter: bool = False):
    ...
```

| Declaration | Behavior |
|---|---|
| `email` (no default) | required: a `400` error is returned when it is missing |
| `age: int = 18` | optional, converted to `int` (`400` if it isn't a number) |
| `newsletter: bool = False` | `"on"`, `"true"`, `"1"`, `"yes"` give `True`; an unchecked checkbox gives `False` |
| `photo` | an uploaded file (`UploadedFile`) when the form sends one |

Supported conversions: `str`, `int`, `float` and `bool`.

## The request object

`request` can be imported from `claide` and used anywhere inside a route. You can also receive it as a parameter named `request`.

```python
from claide import request

@post("/search/<category>")
def search(category):
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
from claide import App, Router

app = App(__name__)
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
