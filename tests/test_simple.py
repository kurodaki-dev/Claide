"""The short way of writing a site: shortcuts, free return values, auto parameters."""

import pytest

import claide
from claide import App, Page, md, request, tags as t


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAIDE_CACHE_DIR", str(tmp_path / "cache"))
    return App("t", root=str(tmp_path))


def test_star_import_exposes_tags():
    ns = {}
    exec("from claide import *", ns)
    for name in ("route", "run", "request", "h1", "p", "div", "a", "button", "form", "input_", "md", "ui"):
        assert name in ns, name
    for risky in ("i", "s", "data", "output", "input", "time"):
        assert risky not in ns, risky
    assert str(ns["h1"]("x")) == "<h1>x</h1>"
    assert str(ns["input_"](name="q")) == '<input name="q">'


def test_tuple_and_list_of_elements_make_a_page(app):
    @app.get("/")
    def home():
        return t.h1("Hello"), t.p("text")

    @app.get("/list")
    def lst():
        return [t.h1("List page")]

    @app.get("/json")
    def js():
        return [1, 2], 201

    c = app.test_client()
    r = c.get("/")
    assert "<h1>Hello</h1><p>text</p>" in r.text and "<title>Hello</title>" in r.text
    assert "<title>List page</title>" in c.get("/list").text
    r = c.get("/json")
    assert r.status == 201 and r.json == [1, 2]


def test_parameters_filled_from_request(app):
    @app.route("/f", methods=["GET", "POST"])
    def f(name: str, age: int = 0, news: bool = False, ratio: float = 1.0):
        return {"name": name, "age": age, "news": news, "ratio": ratio}

    c = app.test_client()
    assert c.post("/f", data={"name": "Ann", "age": "31", "news": "on", "ratio": "0.5"}).json == \
        {"name": "Ann", "age": 31, "news": True, "ratio": 0.5}
    assert c.get("/f?name=Bob").json == {"name": "Bob", "age": 0, "news": False, "ratio": 1.0}
    assert c.post("/f", json_data={"name": "Cy", "age": 4}).json["age"] == 4
    assert c.get("/f").status == 400            # missing required value
    assert c.get("/f?name=x&age=old").status == 400   # wrong type


def test_url_params_win_over_query(app):
    @app.get("/u/<int:uid>")
    def u(uid):
        return {"uid": uid}

    assert app.test_client().get("/u/3?uid=9").json == {"uid": 3}


def test_global_request(app):
    @app.get("/who")
    def who():
        return {"q": request.args.get("q"), "method": request.method}

    assert app.test_client().get("/who?q=hi").json == {"q": "hi", "method": "GET"}
    with pytest.raises(RuntimeError):
        request.path


def test_sessions_without_secret_key(app):
    @app.get("/n")
    def n():
        request.session["n"] = request.session.get("n", 0) + 1
        return str(request.session["n"])

    c = app.test_client()
    assert [c.get("/n").text for _ in range(3)] == ["1", "2", "3"]
    key = app.secret_key
    assert key and App("t", root=app.root).get_secret_key() == key  # same key after a restart


def test_static_files_linked_automatically(tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "style.css").write_text("body{}")
    (static / "script.js").write_text("")
    (static / "favicon.svg").write_text("<svg/>")
    app = App("t", root=str(tmp_path))

    @app.get("/")
    def home():
        return t.h1("x")

    html = app.test_client().get("/").text
    assert 'href="/static/style.css"' in html and 'src="/static/script.js"' in html
    assert 'rel="icon" href="/static/favicon.svg"' in html
    off = App("t", root=str(tmp_path), auto_static=False)
    off.get("/")(lambda: t.h1("x"))
    assert "style.css" not in off.test_client().get("/").text


def test_theme(tmp_path):
    app = App("t", root=str(tmp_path), theme=True)
    app.get("/")(lambda: t.h1("x"))
    assert "--c-accent" in app.test_client().get("/").text


def test_markdown():
    html = str(md("""
        # Title

        Some **bold**, `code` and a [link](/x).

        - one
        - two
    """))
    assert '<h1>Title</h1>' in html
    assert "<strong>bold</strong>" in html and "<code>code</code>" in html
    assert '<a href="/x">link</a>' in html and "<li>two</li>" in html
    assert "&lt;script&gt;" in str(md("<script>"))


def test_shortcuts(tmp_path, monkeypatch):
    from claide import quick

    monkeypatch.setattr(quick, "_app", None)

    @claide.route("/")
    def home():
        if request.method == "POST":
            return t.h1("Posted")
        return t.h1("Home")

    @claide.error(404)
    def nf():
        return t.h1("Nope")

    app = claide.default_app()
    c = app.test_client()
    assert "<h1>Home</h1>" in c.get("/").text
    assert "<h1>Posted</h1>" in c.post("/").text      # route() accepts GET and POST
    r = c.get("/missing")
    assert r.status == 404 and "<h1>Nope</h1>" in r.text
    assert "--c-accent" in c.get("/").text            # default theme on
    monkeypatch.setattr(quick, "_app", None)


def test_page_without_title_in_app(app):
    @app.get("/")
    def home():
        return Page(None, t.p("no heading"))

    assert "<title>Untitled</title>" in app.test_client().get("/").text
    named = App("t", root=app.root, title="Shop")
    named.get("/")(lambda: t.h1("Cart"))
    assert "<title>Cart · Shop</title>" in named.test_client().get("/").text


def test_run_does_nothing_when_imported(monkeypatch):
    from claide import quick

    monkeypatch.setattr(quick, "_app", None)
    started = []
    monkeypatch.setattr(App, "run", lambda self, *a, **k: started.append(True))
    ns = {"__name__": "some_module"}
    exec("from claide import *\n@route('/')\ndef home():\n    return h1('x')\napp = run()", ns)
    assert started == [] and ns["app"] is claide.default_app()
    exec("from claide import run\nrun()", {"__name__": "__main__"})
    assert started == [True]
    monkeypatch.setattr(quick, "_app", None)
