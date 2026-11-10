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

Sessions are stored in a cookie signed with HMAC: users can read it but cannot modify it. Give your app a secret key:

```python
app = App(__name__, secret_key="a-long-random-string")

@app.get("/")
def home(request):
    request.session["visits"] = request.session.get("visits", 0) + 1
    return f"Visit number {request.session['visits']}"
```

> Generate a key with `python -c "import secrets; print(secrets.token_hex(32))"`, or set the `CLAIDE_SECRET_KEY` environment variable. Never commit a production key.

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
