"""Splitting a site into several files with a routes/ folder."""

import textwrap

import pytest

import claide
from claide import App


def write(path, code):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(code))


@pytest.fixture(autouse=True)
def isolated_default_app(monkeypatch, tmp_path):
    from claide import quick

    monkeypatch.setenv("CLAIDE_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(quick, "_app", None)
    yield
    monkeypatch.setattr(quick, "_app", None)


def test_shortcut_routes_in_several_files(tmp_path):
    write(tmp_path / "routes" / "blog.py", """
        from claide import *

        @route("/blog")
        def blog():
            return h1("Blog")
    """)
    write(tmp_path / "routes" / "api" / "users.py", """
        from claide import get

        @get("/api/users")
        def users():
            return [{"id": 1}]
    """)
    write(tmp_path / "routes" / "_draft.py", "raise RuntimeError('must not be imported')")
    write(tmp_path / "app.py", """
        from claide import *

        @route("/")
        def home():
            return h1("Home")

        app = run()
    """)
    ns = {"__name__": "site_app", "__file__": str(tmp_path / "app.py")}
    exec(compile((tmp_path / "app.py").read_text(), ns["__file__"], "exec"), ns)
    app = ns["app"]
    c = app.test_client()
    assert "<h1>Home</h1>" in c.get("/").text
    assert "<h1>Blog</h1>" in c.get("/blog").text
    assert c.get("/api/users").json == [{"id": 1}]
    assert app.url_for("blog") == "/blog"


def test_explicit_app_with_router_and_shortcuts(tmp_path):
    write(tmp_path / "routes" / "shop.py", """
        from claide import Router, h1, route

        router = Router("/shop")

        @router.get("/")
        def shop():
            return h1("Shop")

        @route("/about")
        def about():
            return h1("About")
    """)
    app = App("explicit", root=str(tmp_path))
    c = app.test_client()
    assert "<h1>Shop</h1>" in c.get("/shop").text
    assert "<h1>About</h1>" in c.get("/about").text
    from claide import quick
    assert quick._app is None  # the routes went to this app, not to the default one


def test_routes_folder_can_be_disabled_or_renamed(tmp_path):
    write(tmp_path / "routes" / "a.py", "from claide import *\n@route('/a')\ndef a():\n    return h1('A')\n")
    write(tmp_path / "pages" / "b.py", "from claide import *\n@route('/b')\ndef b():\n    return h1('B')\n")
    off = App("off", root=str(tmp_path), routes_folder=None)
    assert off.test_client().get("/a").status == 404
    other = App("other", root=str(tmp_path), routes_folder="pages")
    assert other.test_client().get("/b").status == 200


def test_build_includes_routes_from_files(tmp_path):
    write(tmp_path / "routes" / "about.py", "from claide import *\n@route('/about')\ndef about():\n    return h1('About')\n")
    app = App("b", root=str(tmp_path))
    app.get("/")(lambda: claide.h1("Home"))
    app.build(str(tmp_path / "dist"))
    assert (tmp_path / "dist" / "about" / "index.html").exists()
