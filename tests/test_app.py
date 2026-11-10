import json

import pytest

from claide import App, HTTPError, Page, Router, abort, redirect, tags as t
from claide.components import Form, Field, Hero


@pytest.fixture
def app(tmp_path):
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "style.css").write_text("body{}")
    app = App("test", root=str(tmp_path), secret_key="secret")
    app.css(app.static("style.css"))

    @app.route("/")
    def home():
        return Page("Home", Hero("Hello"))

    @app.get("/user/<int:uid>")
    def user(uid, request):
        return {"uid": uid, "q": request.args.get("q")}

    @app.route("/form", methods=["GET", "POST"])
    def form(request):
        if request.method == "POST":
            return f"Thanks {request.form['name']}"
        return Page("Form", Form(Field("Name", "name")))

    @app.post("/api/echo")
    def echo(request):
        return request.json, 201

    @app.get("/count")
    def count(request):
        request.session["n"] = request.session.get("n", 0) + 1
        return str(request.session["n"])

    @app.get("/go")
    def go():
        return redirect("/")

    @app.get("/secret")
    def secret():
        abort(403)

    @app.get("/boom")
    def boom():
        raise RuntimeError("x")

    @app.get("/stream")
    def stream():
        return (f"{i}" for i in range(3))

    return app


def test_page(app):
    r = app.test_client().get("/")
    assert r.status == 200
    assert "text/html" in r.content_type
    assert '<link rel="stylesheet" href="/static/style.css">' in r.text
    assert "cl-hero" in r.text


def test_params_and_json(app):
    r = app.test_client().get("/user/42?q=x")
    assert r.json == {"uid": 42, "q": "x"}
    assert app.test_client().get("/user/abc").status == 404


def test_form_and_methods(app):
    c = app.test_client()
    assert 'name="name"' in c.get("/form").text
    assert c.post("/form", data={"name": "Léa"}).text == "Thanks Léa"
    assert c.delete("/form").status == 405


def test_json_body(app):
    r = app.test_client().post("/api/echo", json_data={"a": 1})
    assert r.status == 201 and r.json == {"a": 1}


def test_session(app):
    c = app.test_client()
    assert c.get("/count").text == "1"
    assert c.get("/count").text == "2"
    c.cookies["claide_session"] = "tampered.abc"
    assert c.get("/count").text == "1"


def test_errors_and_redirect(app):
    c = app.test_client()
    assert c.get("/go").status == 302
    assert c.get("/secret").status == 403
    assert c.get("/boom").status == 500
    assert c.get("/nope").status == 404
    assert c.get("/api/nope").json["status"] == 404


def test_error_handler(app):
    @app.errorhandler(404)
    def nf():
        return Page("Lost", t.h1("Lost!"))

    r = app.test_client().get("/nope")
    assert r.status == 404 and "Lost!" in r.text


def test_static(app):
    c = app.test_client()
    assert c.get("/static/style.css").text == "body{}"
    assert c.get("/static/../app.py").status == 404


def test_streaming(app):
    assert app.test_client().get("/stream").text == "012"


def test_hooks_layout_router(app):
    api = Router("/v1")

    @api.get("/ping")
    def ping():
        return {"pong": True}

    app.include(api)

    @app.before_request
    def block(request):
        if request.path == "/blocked":
            return "no", 401

    @app.layout
    def layout(page):
        page.add(t.footer("bottom"))

    c = app.test_client()
    assert c.get("/v1/ping").json == {"pong": True}
    assert c.get("/blocked").status == 401
    assert "<footer>bottom</footer>" in c.get("/").text
    assert app.url_for("user", uid=3, q="a") == "/user/3?q=a"


def test_build(app, tmp_path):
    out = tmp_path / "dist"
    app.build(str(out))
    assert (out / "index.html").exists()
    assert (out / "form" / "index.html").exists()
    assert (out / "static" / "style.css").exists()


def test_base_path(tmp_path):
    app = App("t", root=str(tmp_path), base_path="Claide/")

    @app.get("/docs/<slug>")
    def doc(slug):
        return slug

    assert app.url("/") == "/Claide/"
    assert app.url("/docs") == "/Claide/docs"
    assert app.url("https://x.io") == "https://x.io"
    assert app.static("a.css") == "/Claide/static/a.css"
    assert app.url_for("doc", slug="intro") == "/Claide/docs/intro"
    c = app.test_client()
    assert c.get("/Claide/docs/intro").text == "intro"
    assert c.get("/docs/intro").text == "intro"
