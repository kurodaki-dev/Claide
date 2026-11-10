"""Runs inside the IDE (Pyodide): loads the user's project and answers preview requests."""

import base64
import mimetypes
import os
import re
import sys
import traceback

import claide
from claide import quick, uitemplate

# Imported now so they are part of the engine snapshot (faster first run).
import claide.cli  # noqa: E402,F401
import claide.components  # noqa: E402,F401
import claide.markdown  # noqa: E402,F401
import claide.theme  # noqa: E402,F401
import importlib.util  # noqa: E402,F401

PROJECT = "/project"
_state = {"app": None, "client": None, "modules": set()}


def _download(url, timeout):
    """Uiverse download through a synchronous XMLHttpRequest (no sockets in WebAssembly)."""
    from js import XMLHttpRequest

    req = XMLHttpRequest.new()
    req.open("GET", url, False)
    try:
        req.send(None)
    except Exception as exc:  # network error
        raise uitemplate.UITemplateError(f"Could not reach GitHub: {exc}") from None
    if req.status == 404:
        return None
    if req.status != 200:
        raise uitemplate.UITemplateError(f"HTTP error {req.status} while downloading {url}")
    return req.responseText


uitemplate._download = _download


def _forget_project_modules():
    for name in list(sys.modules):
        mod = sys.modules[name]
        path = getattr(mod, "__file__", "") or ""
        if path.startswith(PROJECT + "/") or name.startswith("claide_routes_"):
            del sys.modules[name]


def load(entry="app.py"):
    """(Re)load the project. Returns the list of routes, or raises with a readable error."""
    _forget_project_modules()
    quick._app = None
    os.chdir(PROJECT)
    if PROJECT not in sys.path:
        sys.path.insert(0, PROJECT)
    path = os.path.join(PROJECT, entry)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{entry} not found. Create it to start your site.")
    import importlib.util

    spec = importlib.util.spec_from_file_location("project_app", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["project_app"] = module
    spec.loader.exec_module(module)  # run() does nothing here: the IDE serves the app
    app = getattr(module, "app", None)
    if not isinstance(app, claide.App):
        app = quick._app
    if app is None:
        raise RuntimeError("No page found. Add a route, for example:\n\n"
                           "@route(\"/\")\ndef home():\n    return h1(\"Hello!\")")
    app.debug = True
    app._ensure_routes()
    _state["app"] = app
    _state["client"] = app.test_client()
    return [{"path": r.path, "methods": sorted(r.methods - {"HEAD"}), "name": r.name} for r in app.routes]


_LINK_CSS = re.compile(r'<link\b[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>')
_SCRIPT_SRC = re.compile(r'<script\b([^>]*)\bsrc="([^"]+)"([^>]*)></script>')
_LOCAL_URL = re.compile(r'(src|href|poster)="(/[^"#?]*)(\?[^"]*)?"')


def _static_file(url):
    app = _state["app"]
    prefix = app.url(app.static_url) + "/"
    if not url.startswith(prefix) or not app.static_folder:
        return None
    path = os.path.normpath(os.path.join(app.static_folder, url[len(prefix):]))
    if not path.startswith(app.static_folder) or not os.path.isfile(path):
        return None
    return path


def _inline_assets(html):
    """The preview has no server: put the project's CSS, JS and images inside the page."""

    def css(m):
        path = _static_file(m.group(1))
        if not path:
            return m.group(0)
        with open(path, encoding="utf-8", errors="replace") as f:
            return f"<style>/* {m.group(1)} */\n{f.read()}\n</style>"

    def script(m):
        path = _static_file(m.group(2))
        if not path:
            return m.group(0)
        with open(path, encoding="utf-8", errors="replace") as f:
            code = f.read().replace("</script", "<\\/script")
        return f"<script{m.group(1)}{m.group(3)}>/* {m.group(2)} */\n{code}\n</script>"

    def media(m):
        path = _static_file(m.group(2))
        if not path:
            return m.group(0)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'{m.group(1)}="data:{mime};base64,{data}"'

    html = _LINK_CSS.sub(css, html)
    html = _SCRIPT_SRC.sub(script, html)
    return _LOCAL_URL.sub(media, html)


def request(method, path, fields=None, body=None, content_type=None):
    """Send a request to the project's app, the way a browser would."""
    client = _state["client"]
    if client is None:
        raise RuntimeError("The project is not running.")
    kwargs = {}
    if fields is not None:
        kwargs["data"] = {k: v for k, v in fields}
        pairs = list(fields)
        if len({k for k, _ in pairs}) != len(pairs):  # repeated names (checkboxes)
            multi = {}
            for k, v in pairs:
                multi.setdefault(k, []).append(v)
            kwargs["data"] = multi
    elif body is not None:
        kwargs["body"] = body.encode("utf-8")
        if content_type:
            kwargs["headers"] = {"Content-Type": content_type}
    resp = client.request(method, path, **kwargs)
    ctype = resp.content_type
    text = resp.text
    if "text/html" in ctype:
        text = _inline_assets(text)
    return {
        "status": resp.status,
        "contentType": ctype,
        "location": resp.get_header("Location"),
        "body": text,
    }


def project_files(known):
    """Files created by the project itself (e.g. Uiverse components saved in templates/)."""
    found = {}
    for dirpath, dirnames, filenames in os.walk(PROJECT):
        dirnames[:] = [d for d in dirnames if d != "__pycache__" and not d.startswith(".")]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, PROJECT)
            if rel in known or name.endswith((".pyc",)):
                continue
            try:
                with open(full, encoding="utf-8") as f:
                    found[rel] = f.read()
            except (UnicodeDecodeError, OSError):
                continue
    return found


def format_error():
    """Last exception as a short traceback that points at the user's files."""
    etype, value, tb = sys.exc_info()
    frames = [f for f in traceback.extract_tb(tb) if f.filename.startswith(PROJECT)]
    lines = [f'  File "{f.filename[len(PROJECT) + 1:]}", line {f.lineno}, in {f.name}\n    {f.line}' for f in frames]
    if isinstance(value, SyntaxError) and value.filename:
        name = value.filename[len(PROJECT) + 1:] if value.filename.startswith(PROJECT) else value.filename
        lines.append(f'  File "{name}", line {value.lineno}\n    {(value.text or "").rstrip()}')
    head = "Traceback (most recent call last):\n" if lines else ""
    return head + "\n".join(lines) + ("\n" if lines else "") + f"{etype.__name__}: {value}"


def new_project_files():
    from claide.cli import APP_TEMPLATE, CSS_TEMPLATE, JS_TEMPLATE

    return {
        "app.py": APP_TEMPLATE.format(name="my site"),
        "static/style.css": CSS_TEMPLATE,
        "static/script.js": JS_TEMPLATE,
    }


def safe(func, *args):
    """Call func and turn any exception into {"ok": False, "error": <short traceback>}."""
    try:
        result = func(*args)
    except BaseException:
        return {"ok": False, "error": format_error()}
    if isinstance(result, dict):
        return {"ok": True, **result}
    return {"ok": True, "routes": result}
