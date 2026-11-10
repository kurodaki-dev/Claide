# Forms, uploads & sessions

## Handling a form

```python
from claide.components import Form, Field, Alert

@app.route("/contact", methods=["GET", "POST"])
def contact(request):
    message = None
    if request.method == "POST":
        message = Alert(f"Thanks {request.form['name']}!", "success")
    return Page("Contact", message, Form(
        Field("Name", "name", required=True),
        Field("Email", "email", type="email"),
        Field("Topic", "topic", type="select", options=["Question", "Bug"]),
        Field("Message", "message", type="textarea"),
        action="/contact",
    ))
```

## File uploads

Add `upload=True` to the form (it sets `enctype="multipart/form-data"`), then read `request.files`:

```python
Form(Field("Avatar", "avatar", type="file"), upload=True)

@app.post("/profile")
def profile(request):
    f = request.files["avatar"]
    f.filename, f.content_type, f.size
    f.save("uploads/")          # directory -> keeps a sanitized file name
    return redirect("/profile")
```

The default maximum request size is 16 MB: change it with `App(max_content_length=...)`.

## Sessions

`request.session` is a dictionary kept between requests for each visitor. It works without any setup:

```python
@route("/")
def home():
    request.session["visits"] = request.session.get("visits", 0) + 1
    return h1(f"Visit number {request.session['visits']}")
```

Sessions are stored in a cookie signed with HMAC: visitors can read it but cannot modify it. During development Claide generates the signing key itself and keeps it in your user cache folder, outside the project, so it is never committed.

> In production, set your own key with the `CLAIDE_SECRET_KEY` environment variable or `App(secret_key=...)`, so that every server uses the same one. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`.

Session values must be JSON-serializable. Use `request.session.pop("key", None)` or `request.session.clear()` to log a user out.

## Cookies

```python
@app.get("/theme/<name>")
def theme(name):
    resp = redirect("/")
    resp.set_cookie("theme", name, max_age=30 * 86400)
    return resp

@app.get("/")
def home(request):
    theme = request.cookies.get("theme", "light")
```
