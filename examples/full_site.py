"""Complete website example built with Claide.

    python examples/full_site.py   ->  http://127.0.0.1:8000
"""

from claide import App, Page, UITemplate, abort, redirect, tags as t
from claide.components import (
    Alert, Button, Card, Field, Footer, Form, Grid, Hero, Navbar, Section,
)

app = App(__name__, secret_key="change-me-in-production")

# Files linked on EVERY page (in examples/static/)
app.css(app.static("style.css"))
app.js(app.static("script.js"))

# Uiverse.io / cssbuttons.io components (downloaded once, then cached).
# Without Internet access, fall back to a button bundled with Claide.
try:
    button = UITemplate("https://uiverse.io/0x-Sarthak/hungry-penguin-30").scoped()
except Exception:
    button = UITemplate.builtin("gradient")

POSTS = {
    1: ("Welcome", "First blog post, written 100% in Python."),
    2: ("Uiverse", "Thousands of CSS components, usable in one line."),
}


@app.layout
def base(page):
    page.body.children.insert(0, Navbar("My Site", [
        ("Home", "/"), ("Blog", "/blog"), ("Contact", "/contact"), ("API", "/api/posts"),
    ]))
    page.add(Footer("© 2026 — Made with Claide"))


@app.route("/")
def home(request):
    return Page(
        "Home",
        Hero(
            "A complete website in Python",
            "Pages, forms, APIs, sessions and Uiverse components.",
            button.text("Contact Us", "Contact me").link("/contact"),
            Button("Read the blog", "/blog", outline=True),
        ),
        Section(
            Grid(*[Card(title, text, href=f"/blog/{i}") for i, (title, text) in POSTS.items()]),
            title="Latest posts", alt=True,
        ),
        description="Claide example website",
    )


@app.get("/blog")
def blog():
    return Page("Blog", Section(
        t.ul([t.li(t.a(title, href=app.url_for("post", pid=i))) for i, (title, _) in POSTS.items()]),
        title="Blog",
    ))


@app.get("/blog/<int:pid>")
def post(pid):
    if pid not in POSTS:
        abort(404)
    title, text = POSTS[pid]
    return Page(title, Section(t.p(text), title=title))


@app.route("/contact", methods=["GET", "POST"])
def contact(request):
    if request.method == "POST":
        request.session["name"] = request.form.get("name", "")
        return redirect("/thanks")
    return Page("Contact", Section(
        Form(
            Field("Name", "name", required=True),
            Field("Email", "email", type="email"),
            Field("Subject", "subject", type="select", options=["Question", "Bug", "Other"]),
            Field("Message", "message", type="textarea"),
        ),
        title="Contact",
    ))


@app.get("/thanks")
def thanks(request):
    return Page("Thanks", Section(Alert(f"Thanks {request.session.get('name', '')}!", "success")))


# --- JSON API --------------------------------------------------------------
@app.get("/api/posts")
def api_posts():
    return [{"id": i, "title": title} for i, (title, _) in POSTS.items()]


@app.post("/api/posts")
def api_create(request):
    data = request.json or {}
    if "title" not in data:
        abort(400, "Field 'title' is required")
    pid = max(POSTS) + 1
    POSTS[pid] = (data["title"], data.get("text", ""))
    return {"id": pid}, 201


@app.errorhandler(404)
def not_found():
    return Page("Not found", Section(t.h1("404"), t.p("This page does not exist."), Button("Home", "/")))


if __name__ == "__main__":
    app.run()
