"""Claide web application: dynamic routes, forms, JSON API, sessions,
static files, uploads, streaming... (WSGI server, zero dependencies).

Example ::

    from claide import App, Page, tags as t

    app = App(__name__, secret_key="change-me")

    @app.route("/")
    def home():
        return Page("Home", t.h1("Hi!"))

    @app.route("/hello/<name>")
    def hello(name):
        return Page(f"Hello {name}", t.h1(f"Hello {name}"))

    @app.post("/api/add")
    def add(request):
        data = request.json
        return {"result": data["a"] + data["b"]}

    app.run()
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import inspect
import json
import mimetypes
import os
import re
import secrets
import shutil
import sys
import threading
import traceback
from email.parser import BytesParser
from email.policy import HTTP
from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple
from urllib.parse import parse_qs, quote

from .html import Asset, Element, escape, iter_assets
from .page import Page

__all__ = [
    "App", "Router", "Request", "Response", "UploadedFile", "HTTPError",
    "redirect", "abort", "send_file", "request",
]


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------
class UploadedFile:
    """File sent through an ``<input type="file">`` form field."""

    def __init__(self, filename: str, content_type: str, data: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self.data = data

    @property
    def size(self) -> int:
        return len(self.data)

    def save(self, path: str) -> str:
        """Save the file. If ``path`` is a directory, keep the (sanitized) original name."""
        if os.path.isdir(path):
            path = os.path.join(path, secure_filename(self.filename))
        with open(path, "wb") as f:
            f.write(self.data)
        return path

    def __repr__(self) -> str:
        return f"<UploadedFile {self.filename!r} {self.size} octets>"


def secure_filename(name: str) -> str:
    name = os.path.basename(name.replace("\\", "/"))
    name = re.sub(r"[^\w.\-]", "_", name).strip("._")
    return name or "file"


class MultiDict(dict):
    """dict that keeps every value: ``d["x"]`` -> first, ``d.getlist("x")`` -> all."""

    def __init__(self, pairs: Iterable[Tuple[str, Any]] = ()) -> None:
        super().__init__()
        self._lists: Dict[str, List[Any]] = {}
        for k, v in pairs:
            self._lists.setdefault(k, []).append(v)
            if k not in self:
                super().__setitem__(k, v)

    def getlist(self, key: str) -> List[Any]:
        return list(self._lists.get(key, []))


class Request:
    """Incoming HTTP request."""

    def __init__(self, environ: dict, app: Optional["App"] = None) -> None:
        self.environ = environ
        self.app = app
        self.method: str = environ.get("REQUEST_METHOD", "GET").upper()
        raw_path = environ.get("PATH_INFO", "/") or "/"
        try:  # WSGI decodes as latin-1, convert back to UTF-8
            raw_path = raw_path.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        self.path: str = raw_path
        self.query_string: str = environ.get("QUERY_STRING", "")
        self.params: Dict[str, Any] = {}
        self._body: Optional[bytes] = None
        self._form: Optional[MultiDict] = None
        self._files: Optional[MultiDict] = None
        self._session: Optional["Session"] = None
        self.g: Dict[str, Any] = {}  # free storage during the request

    # -- headers -------------------------------------------------------------
    @property
    def headers(self) -> Dict[str, str]:
        h = {}
        for k, v in self.environ.items():
            if k.startswith("HTTP_"):
                h[k[5:].replace("_", "-").title()] = v
        if "CONTENT_TYPE" in self.environ:
            h["Content-Type"] = self.environ["CONTENT_TYPE"]
        if "CONTENT_LENGTH" in self.environ:
            h["Content-Length"] = self.environ["CONTENT_LENGTH"]
        return h

    @property
    def content_type(self) -> str:
        return self.environ.get("CONTENT_TYPE", "") or ""

    @property
    def host(self) -> str:
        return self.environ.get("HTTP_HOST") or self.environ.get("SERVER_NAME", "")

    @property
    def url(self) -> str:
        scheme = self.environ.get("wsgi.url_scheme", "http")
        qs = f"?{self.query_string}" if self.query_string else ""
        return f"{scheme}://{self.host}{quote(self.path)}{qs}"

    @property
    def remote_addr(self) -> str:
        return self.environ.get("REMOTE_ADDR", "")

    @property
    def is_json(self) -> bool:
        return "json" in self.content_type

    # -- data ----------------------------------------------------------------
    @property
    def args(self) -> MultiDict:
        """URL query parameters (``?page=2``)."""
        return MultiDict(
            (k, v) for k, vs in parse_qs(self.query_string, keep_blank_values=True).items() for v in vs
        )

    query = args

    @property
    def body(self) -> bytes:
        if self._body is None:
            try:
                length = int(self.environ.get("CONTENT_LENGTH") or 0)
            except ValueError:
                length = 0
            max_size = self.app.max_content_length if self.app else None
            if max_size is not None and length > max_size:
                raise HTTPError(413, "Request body too large")
            stream = self.environ.get("wsgi.input")
            self._body = stream.read(length) if (stream and length > 0) else b""
        return self._body

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    @property
    def json(self) -> Any:
        """Request body decoded as JSON (``None`` if empty)."""
        if not self.body:
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            raise HTTPError(400, "Invalid JSON") from None

    def _parse_form(self) -> None:
        self._form, self._files = MultiDict(), MultiDict()
        ctype = self.content_type
        if ctype.startswith("application/x-www-form-urlencoded"):
            pairs = parse_qs(self.text, keep_blank_values=True)
            self._form = MultiDict((k, v) for k, vs in pairs.items() for v in vs)
        elif ctype.startswith("multipart/form-data"):
            msg = BytesParser(policy=HTTP).parsebytes(
                f"Content-Type: {ctype}\r\n\r\n".encode("latin-1") + self.body
            )
            fields, files = [], []
            for part in msg.iter_parts():
                name = part.get_param("name", header="content-disposition")
                if not name:
                    continue
                filename = part.get_filename()
                payload = part.get_payload(decode=True) or b""
                if filename is not None:
                    files.append((name, UploadedFile(filename, part.get_content_type(), payload)))
                else:
                    charset = part.get_content_charset() or "utf-8"
                    fields.append((name, payload.decode(charset, errors="replace")))
            self._form, self._files = MultiDict(fields), MultiDict(files)

    @property
    def form(self) -> MultiDict:
        """Fields of a POST form (urlencoded or multipart)."""
        if self._form is None:
            self._parse_form()
        return self._form  # type: ignore[return-value]

    @property
    def files(self) -> MultiDict:
        """Uploaded files (``request.files["avatar"].save("uploads/")``)."""
        if self._files is None:
            self._parse_form()
        return self._files  # type: ignore[return-value]

    def get(self, key: str, default: Any = None) -> Any:
        """Look up a value in URL params, form, JSON body, then query string."""
        if key in self.params:
            return self.params[key]
        if self.method in ("POST", "PUT", "PATCH", "DELETE"):
            if self.is_json and isinstance(self.json, dict) and key in self.json:
                return self.json[key]
            if key in self.form:
                return self.form[key]
        return self.args.get(key, default)

    @property
    def cookies(self) -> Dict[str, str]:
        jar = SimpleCookie()
        try:
            jar.load(self.environ.get("HTTP_COOKIE", ""))
        except Exception:  # malformed cookie
            return {}
        return {k: m.value for k, m in jar.items()}

    @property
    def session(self) -> "Session":
        """User session stored in a signed cookie."""
        if self._session is None:
            if not self.app:
                raise RuntimeError("Sessions need an App.")
            key = self.app.get_secret_key()
            self._session = Session.load(self.cookies.get(self.app.session_cookie, ""), key)
        return self._session

    def __repr__(self) -> str:
        return f"<Request {self.method} {self.path}>"


class Session(dict):
    """dict saved in an HMAC-signed cookie (readable but tamper-proof)."""

    modified = False

    def __setitem__(self, key: str, value: Any) -> None:
        self.modified = True
        super().__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        self.modified = True
        super().__delitem__(key)

    def clear(self) -> None:
        self.modified = True
        super().clear()

    def pop(self, *args: Any) -> Any:
        self.modified = True
        return super().pop(*args)

    def update(self, *args: Any, **kwargs: Any) -> None:
        self.modified = True
        super().update(*args, **kwargs)

    @staticmethod
    def _sign(data: bytes, key: str) -> str:
        return hmac.new(key.encode(), data, hashlib.sha256).hexdigest()

    @classmethod
    def load(cls, cookie: str, key: str) -> "Session":
        s = cls()
        if cookie and "." in cookie:
            payload, sig = cookie.rsplit(".", 1)
            if hmac.compare_digest(cls._sign(payload.encode(), key), sig):
                try:
                    dict.update(s, json.loads(base64.urlsafe_b64decode(payload.encode())))
                except ValueError:
                    pass
        return s

    def dump(self, key: str) -> str:
        payload = base64.urlsafe_b64encode(json.dumps(self, separators=(",", ":")).encode()).decode()
        return f"{payload}.{self._sign(payload.encode(), key)}"


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------
class HTTPError(Exception):
    """Raise an HTTP error: ``raise HTTPError(404)`` or ``abort(403)``."""

    def __init__(self, status: int = 500, message: Optional[str] = None) -> None:
        self.status = status
        try:
            phrase = HTTPStatus(status).phrase
        except ValueError:
            phrase = "Error"
        self.message = message or phrase
        super().__init__(f"{status} {self.message}")


def abort(status: int, message: Optional[str] = None) -> None:
    raise HTTPError(status, message)


class Response:
    """HTTP response. ``body`` may be str, bytes or an iterable (streaming)."""

    def __init__(
        self,
        body: Any = b"",
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> None:
        self.body = body
        self.status = status
        self.headers: List[Tuple[str, str]] = list((headers or {}).items())
        if content_type:
            self.set_header("Content-Type", content_type)
        elif not self.get_header("Content-Type"):
            self.headers.append(("Content-Type", "text/html; charset=utf-8"))

    def get_header(self, name: str) -> Optional[str]:
        for k, v in self.headers:
            if k.lower() == name.lower():
                return v
        return None

    def set_header(self, name: str, value: str) -> "Response":
        self.headers = [(k, v) for k, v in self.headers if k.lower() != name.lower()]
        self.headers.append((name, value))
        return self

    @property
    def content_type(self) -> str:
        return self.get_header("Content-Type") or ""

    def set_cookie(
        self, name: str, value: str, max_age: Optional[int] = None, path: str = "/",
        httponly: bool = True, secure: bool = False, samesite: Optional[str] = "Lax",
    ) -> "Response":
        c = SimpleCookie()
        c[name] = value
        m = c[name]
        m["path"] = path
        if max_age is not None:
            m["max-age"] = max_age
        if httponly:
            m["httponly"] = True
        if secure:
            m["secure"] = True
        if samesite:
            m["samesite"] = samesite
        self.headers.append(("Set-Cookie", m.OutputString()))
        return self

    def delete_cookie(self, name: str, path: str = "/") -> "Response":
        return self.set_cookie(name, "", max_age=0, path=path)

    @property
    def status_line(self) -> str:
        try:
            return f"{self.status} {HTTPStatus(self.status).phrase}"
        except ValueError:
            return f"{self.status} Unknown"

    def iter_body(self) -> Iterator[bytes]:
        body = self.body
        if body is None:
            return
        if isinstance(body, bytes):
            yield body
        elif isinstance(body, str):
            yield body.encode("utf-8")
        else:
            for chunk in body:
                yield chunk.encode("utf-8") if isinstance(chunk, str) else chunk

    @property
    def data(self) -> bytes:
        """Full body (handy in tests)."""
        return b"".join(self.iter_body())

    @property
    def text(self) -> str:
        return self.data.decode("utf-8", errors="replace")

    @property
    def json(self) -> Any:
        return json.loads(self.data)

    def __repr__(self) -> str:
        return f"<Response {self.status_line}>"


def redirect(location: str, status: int = 302) -> Response:
    return Response(b"", status, {"Location": location})


def send_file(path: str, download_name: Optional[str] = None, as_attachment: bool = False,
              max_age: Optional[int] = None) -> Response:
    """Send a file from disk (with the right MIME type)."""
    if not os.path.isfile(path):
        raise HTTPError(404)
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
        ctype += "; charset=utf-8"
    with open(path, "rb") as f:
        data = f.read()
    resp = Response(data, 200, content_type=ctype)
    if as_attachment or download_name:
        name = download_name or os.path.basename(path)
        resp.set_header("Content-Disposition", f"{'attachment' if as_attachment else 'inline'}; filename=\"{name}\"")
    if max_age is not None:
        resp.set_header("Cache-Control", f"public, max-age={max_age}")
    return resp


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------
_CONVERTERS = {
    "str": (r"[^/]+", str),
    "int": (r"-?\d+", int),
    "float": (r"-?\d+(?:\.\d+)?", float),
    "path": (r".+", str),
    "slug": (r"[\w-]+", str),
}
_PARAM_RE = re.compile(r"<(?:(\w+):)?(\w+)>")


class Route:
    def __init__(self, path: str, handler: Callable, methods: Iterable[str], name: Optional[str] = None) -> None:
        self.path = path
        self.handler = handler
        self.methods = {m.upper() for m in methods}
        if "GET" in self.methods:
            self.methods.add("HEAD")
        self.name = name or handler.__name__
        self.converters: Dict[str, Callable] = {}
        pattern, pos = "", 0
        for m in _PARAM_RE.finditer(path):
            pattern += re.escape(path[pos:m.start()])
            conv = m.group(1) or "str"
            if conv not in _CONVERTERS:
                raise ValueError(f"Unknown converter '{conv}' in {path!r}")
            regex, func = _CONVERTERS[conv]
            pattern += f"(?P<{m.group(2)}>{regex})"
            self.converters[m.group(2)] = func
            pos = m.end()
        pattern += re.escape(path[pos:])
        self.regex = re.compile(f"^{pattern}$")
        self.is_static = not self.converters

    def match(self, path: str) -> Optional[Dict[str, Any]]:
        m = self.regex.match(path)
        if not m:
            return None
        try:
            return {k: self.converters[k](v) for k, v in m.groupdict().items()}
        except ValueError:
            return None

    def build(self, **params: Any) -> str:
        def sub(m: "re.Match[str]") -> str:
            key = m.group(2)
            if key not in params:
                raise KeyError(f"Missing parameter '{key}' for route {self.name!r}")
            return quote(str(params.pop(key)), safe="/" if m.group(1) == "path" else "")
        url = _PARAM_RE.sub(sub, self.path)
        if params:
            url += "?" + "&".join(f"{quote(str(k))}={quote(str(v))}" for k, v in params.items())
        return url


class Router:
    """Reusable group of routes, mounted on an App with a prefix.

    ::

        api = Router(prefix="/api")

        @api.get("/users")
        def users():
            return [{"id": 1}]

        app.include(api)
    """

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix.rstrip("/")
        self.routes: List[Route] = []

    def route(self, path: str, methods: Iterable[str] = ("GET",), name: Optional[str] = None) -> Callable:
        def decorator(func: Callable) -> Callable:
            self.add_route(path, func, methods, name)
            return func
        return decorator

    def add_route(self, path: str, handler: Callable, methods: Iterable[str] = ("GET",),
                  name: Optional[str] = None) -> Route:
        full = (self.prefix + path) if path != "/" or not self.prefix else (self.prefix or "/")
        route = Route(full or "/", handler, methods, name)
        self.routes.append(route)
        return route

    def get(self, path: str, **kw: Any) -> Callable:
        return self.route(path, ("GET",), **kw)

    def post(self, path: str, **kw: Any) -> Callable:
        return self.route(path, ("POST",), **kw)

    def put(self, path: str, **kw: Any) -> Callable:
        return self.route(path, ("PUT",), **kw)

    def patch(self, path: str, **kw: Any) -> Callable:
        return self.route(path, ("PATCH",), **kw)

    def delete(self, path: str, **kw: Any) -> Callable:
        return self.route(path, ("DELETE",), **kw)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
_local = threading.local()


class _RequestProxy:
    """``from claide import request``: the request being handled in this thread."""

    def _get(self) -> Request:
        req = getattr(_local, "request", None)
        if req is None:
            raise RuntimeError("'request' can only be used while handling a request (inside a route).")
        return req

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get(), name)

    def __repr__(self) -> str:
        req = getattr(_local, "request", None)
        return repr(req) if req is not None else "<request: none>"


request = _RequestProxy()


def _first_heading(node: Any) -> Optional[str]:
    """Text of the first <h1> found in a tree of elements."""
    stack = [node]
    while stack:
        el = stack.pop(0)
        if isinstance(el, Element):
            if el.tag == "h1":
                return _text_of(el).strip() or None
            stack[0:0] = list(el.children)
    return None


def _text_of(node: Any) -> str:
    if isinstance(node, Element):
        return "".join(_text_of(c) for c in node.children)
    if isinstance(node, (str, int, float)) and not hasattr(node, "__html__"):
        return str(node)
    return ""


_TRUE = {"1", "true", "on", "yes", "y"}
_FALSE = {"0", "false", "off", "no", "n", ""}


def _convert(value: Any, annotation: Any, name: str) -> Any:
    target = annotation
    if isinstance(target, str):
        target = {"int": int, "float": float, "bool": bool, "str": str}.get(target, None)
    if target is None or target is inspect.Parameter.empty or isinstance(value, UploadedFile):
        return value
    try:
        if target is bool:
            if isinstance(value, bool):
                return value
            text = str(value).strip().lower()
            if text in _TRUE:
                return True
            if text in _FALSE:
                return False
            raise ValueError(value)
        if target in (int, float):
            return target(value)
        if target is str:
            return str(value)
    except (TypeError, ValueError):
        raise HTTPError(400, f"Invalid value for '{name}': expected {target.__name__}") from None
    return value


def _params_from_request(func: Callable, params: Any, given: Dict[str, Any], req: Request) -> Dict[str, Any]:
    """Fill the remaining parameters of a route function from the request.

    ``def contact(name, age: int = 0)`` receives ``name`` and ``age`` from the
    form, the JSON body or the query string, converted to the annotated type.
    """
    filled: Dict[str, Any] = {}
    for pname, param in params.items():
        if pname in given or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        value: Any = None
        if req.method in ("POST", "PUT", "PATCH", "DELETE") and req.content_type.startswith("multipart/") \
                and pname in req.files:
            value = req.files[pname]
        if value is None:
            value = req.get(pname)
        if value is None:
            if param.default is param.empty:
                if param.annotation is bool or param.annotation == "bool":
                    filled[pname] = False  # an unchecked checkbox is not sent at all
                    continue
                raise HTTPError(400, f"Missing value for '{pname}'")
            continue
        filled[pname] = _convert(value, param.annotation, pname)
    return filled


class App(Router):
    """Complete web application (WSGI compatible: gunicorn, waitress, uWSGI...)."""

    def __init__(
        self,
        name: Optional[str] = None,
        *,
        static_folder: Optional[str] = "static",
        static_url: str = "/static",
        root: Optional[str] = None,
        secret_key: Optional[str] = None,
        title: Optional[str] = None,
        lang: str = "en",
        max_content_length: Optional[int] = 16 * 1024 * 1024,
        base_path: str = "",
        theme: bool = False,
        auto_static: bool = True,
        favicon: Optional[str] = None,
    ) -> None:
        super().__init__("")
        name = name or "__main__"
        self.name = name
        if root is None:
            mod = sys.modules.get(name)
            mod_file = getattr(mod, "__file__", None)
            root = os.path.dirname(os.path.abspath(mod_file)) if mod_file else os.getcwd()
        self.root = root
        self.static_folder = os.path.join(root, static_folder) if static_folder else None
        self.static_url = "/" + static_url.strip("/")
        self.secret_key = secret_key or os.environ.get("CLAIDE_SECRET_KEY")
        self.session_cookie = "claide_session"
        # Site name added after the <h1> in page titles ("Contact · My shop").
        self.title = title
        self.lang = lang
        self.max_content_length = max_content_length
        # URL prefix when the site is not served at the domain root,
        # e.g. "/MyRepo" for a GitHub Pages project site.
        self.base_path = "/" + base_path.strip("/") if base_path.strip("/") else ""
        self.debug = False
        self._assets: List[Asset] = []
        self._layout: Optional[Callable[[Page], Any]] = None
        self._before: List[Callable] = []
        self._after: List[Callable] = []
        self._error_handlers: Dict[int, Callable] = {}
        self.favicon = favicon
        if theme:
            from .theme import THEME_CSS  # local import: optional feature

            self._assets.append(("style", THEME_CSS))
        if auto_static:
            self._link_static_files()

    def _link_static_files(self) -> None:
        """Link static/style.css, static/script.js and static/favicon.* automatically."""
        folder = self.static_folder
        if not folder or not os.path.isdir(folder):
            return
        if os.path.isfile(os.path.join(folder, "style.css")):
            self.css(self.static("style.css"))
        if os.path.isfile(os.path.join(folder, "script.js")):
            self.js(self.static("script.js"))
        if self.favicon is None:
            for name in ("favicon.svg", "favicon.png", "favicon.ico"):
                if os.path.isfile(os.path.join(folder, name)):
                    self.favicon = self.static(name)
                    break

    def get_secret_key(self) -> str:
        """Key that signs session cookies.

        Uses ``App(secret_key=...)`` or the ``CLAIDE_SECRET_KEY`` environment
        variable. Without one, a random key is generated once and kept in your
        user cache folder (outside the project, so it is never committed).
        """
        if self.secret_key:
            return self.secret_key
        cache = os.environ.get("CLAIDE_CACHE_DIR") or os.path.join(
            os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache"), "claide"
        )
        path = os.path.join(cache, "secrets", hashlib.sha256(self.root.encode()).hexdigest()[:16])
        try:
            with open(path, encoding="utf-8") as f:
                self.secret_key = f.read().strip() or None
        except OSError:
            pass
        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.secret_key)
            except OSError:
                pass  # read-only system: the key only lives as long as the process
        return self.secret_key

    # -- configuration -------------------------------------------------------
    def css(self, *hrefs: str) -> "App":
        """Stylesheet(s) added to EVERY page: ``app.css("/static/style.css")``."""
        self._assets.extend(("css", h) for h in hrefs)
        return self

    def js(self, *srcs: str) -> "App":
        """Script(s) added to EVERY page: ``app.js("/static/script.js")``."""
        self._assets.extend(("js", s) for s in srcs)
        return self

    def style(self, css: str) -> "App":
        self._assets.append(("style", css))
        return self

    def script(self, code: str) -> "App":
        self._assets.append(("script", code))
        return self

    def use(self, *templates: Any) -> "App":
        """Load the CSS/JS of components (UITemplate...) on every page."""
        for t in templates:
            self._assets.extend(iter_assets(t))
        return self

    def static(self, filename: str) -> str:
        """URL of a static file: ``app.static("style.css")`` -> ``/static/style.css``."""
        return self.url(f"{self.static_url}/{filename.lstrip('/')}")

    def url(self, path: str = "/") -> str:
        """Absolute URL of an internal path, including ``base_path``.

        ``App(base_path="/Claide").url("/docs")`` -> ``/Claide/docs``.
        External URLs and anchors are returned unchanged.
        """
        if not path.startswith("/") or path.startswith("//") or not self.base_path:
            return path
        return self.base_path + (path if path != "/" else "/")

    def layout(self, func: Callable[[Page], Any]) -> Callable:
        """Decorator: function called on every Page before rendering (navbar, footer...).

        ::

            @app.layout
            def base(page):
                page.body.children.insert(0, navbar)
                page.add(footer)
        """
        self._layout = func
        return func

    def before_request(self, func: Callable) -> Callable:
        """Run before every request. If it returns a value, that value is the response."""
        self._before.append(func)
        return func

    def after_request(self, func: Callable) -> Callable:
        """Run after every request: ``func(request, response)`` -> response."""
        self._after.append(func)
        return func

    def errorhandler(self, status: int) -> Callable:
        """Custom page for an error code: ``@app.errorhandler(404)``."""
        def decorator(func: Callable) -> Callable:
            self._error_handlers[status] = func
            return func
        return decorator

    def include(self, router: Router, prefix: str = "") -> "App":
        """Mount a ``Router`` on the application."""
        for r in router.routes:
            path = prefix.rstrip("/") + r.path if prefix else r.path
            self.routes.append(Route(path or "/", r.handler, r.methods - {"HEAD"}, r.name))
        return self

    def page(self, path: str, page: Any, name: Optional[str] = None) -> "App":
        """Register a fixed page without writing a function: ``app.page("/about", Page(...))``."""
        self.add_route(path, lambda: page, ("GET",), name or f"page:{path}")
        return self

    def url_for(self, name: str, **params: Any) -> str:
        """Build the URL of a route from its function name."""
        if name == "static":
            return self.static(params.pop("filename"))
        for r in self.routes:
            if r.name == name:
                return self.url(r.build(**params))
        raise KeyError(f"No route named {name!r}")

    # -- handling ------------------------------------------------------------
    @staticmethod
    def current_request() -> Optional[Request]:
        """Current request (in the current thread)."""
        return getattr(_local, "request", None)

    def _call(self, func: Callable, request: Request, _fill: bool = False, **kwargs: Any) -> Any:
        try:
            sig = inspect.signature(func)
        except (TypeError, ValueError):
            return func(**kwargs)
        params = sig.parameters
        accepts_any = any(p.kind is p.VAR_KEYWORD for p in params.values())
        call_kwargs = {k: v for k, v in kwargs.items() if accepts_any or k in params}
        for pname in ("request", "req"):
            if pname in params and pname not in call_kwargs:
                call_kwargs[pname] = request
        if _fill:
            call_kwargs.update(_params_from_request(func, params, call_kwargs, request))
        return func(**call_kwargs)

    def make_response(self, value: Any, request: Optional[Request] = None) -> Response:
        """Convert a route's return value into a ``Response``."""
        status, headers = 200, {}
        if isinstance(value, tuple):
            if 2 <= len(value) <= 3 and isinstance(value[1], int) and not isinstance(value[1], bool):
                value, status, *rest = value  # (body, status) or (body, status, headers)
                if rest:
                    headers = rest[0]
            else:
                value = list(value)  # return h1(...), p(...)  -> several elements
        if isinstance(value, list) and any(hasattr(v, "__html__") for v in value):
            value = Page(None, *value)  # a list of elements is a page, not JSON
        if isinstance(value, Response):
            resp = value
            if status != 200:
                resp.status = status
        elif isinstance(value, Page):
            resp = Response(self.render_page(value), status)
        elif value is None:
            resp = Response(b"", 204 if status == 200 else status)
        elif isinstance(value, (dict, list)):
            resp = Response(json.dumps(value, ensure_ascii=False, default=str), status,
                            content_type="application/json; charset=utf-8")
        elif isinstance(value, (str, bytes)):
            resp = Response(value, status)
        elif hasattr(value, "__html__"):
            # Element, UITemplate, Fragment... -> wrapped in a Page
            resp = Response(self.render_page(Page(None, value)), status)
        elif inspect.isgenerator(value) or hasattr(value, "__iter__"):
            resp = Response(value, status)  # streaming
        else:
            resp = Response(str(value), status, content_type="text/plain; charset=utf-8")
        for k, v in headers.items():
            resp.set_header(k, v)
        return resp

    def render_page(self, page: Page) -> str:
        if page.title is None:
            heading = _first_heading(page.body)
            if heading and self.title and heading != self.title:
                page.title = f"{heading} · {self.title}"
            else:
                page.title = heading or self.title or "Untitled"
        if page.lang is None:
            page.lang = self.lang
        if page.favicon is None and self.favicon:
            page.favicon = self.favicon
        if self._layout is not None:
            result = self._layout(page)
            if isinstance(result, Page):
                page = result
        return page.render(extra_assets=self._assets)

    def _error_response(self, request: Request, err: HTTPError) -> Response:
        handler = self._error_handlers.get(err.status)
        if handler is not None:
            resp = self.make_response(self._call(handler, request, error=err), request)
            if resp.status == 200:
                resp.status = err.status
            return resp
        wants_json = request.path.startswith("/api") or "application/json" in request.environ.get("HTTP_ACCEPT", "")
        if wants_json:
            return self.make_response(({"error": err.message, "status": err.status}, err.status))
        page = Page(f"{err.status} - {err.message}", lang=self.lang, body_attrs={
            "style": "font-family:system-ui,sans-serif;display:grid;place-items:center;min-height:90vh;"
                     "margin:0;background:#fafafa;color:#111"
        })
        page.add(Element("div", Element("h1", str(err.status), style="font-size:4rem;margin:0"),
                         Element("p", err.message), style="text-align:center"))
        return Response(self.render_page(page), err.status)

    def _serve_static(self, path: str) -> Optional[Response]:
        if not self.static_folder or not path.startswith(self.static_url + "/"):
            return None
        rel = path[len(self.static_url) + 1:]
        base = os.path.realpath(self.static_folder)
        full = os.path.realpath(os.path.join(base, rel))
        if not full.startswith(base + os.sep) or not os.path.isfile(full):
            raise HTTPError(404)
        return send_file(full, max_age=0 if self.debug else 3600)

    def dispatch(self, request: Request) -> Response:
        try:
            static = self._serve_static(request.path)
            if static is not None:
                return static
            for hook in self._before:
                rv = self._call(hook, request)
                if rv is not None:
                    return self.make_response(rv, request)
            allowed: set = set()
            for route in self.routes:
                params = route.match(request.path)
                if params is None:
                    continue
                if request.method not in route.methods and request.method != "OPTIONS":
                    allowed |= route.methods
                    continue
                if request.method == "OPTIONS":
                    allowed |= route.methods
                    continue
                request.params = params
                return self.make_response(self._call(route.handler, request, _fill=True, **params), request)
            if allowed:
                if request.method == "OPTIONS":
                    return Response(b"", 204, {"Allow": ", ".join(sorted(allowed | {"OPTIONS"}))})
                resp = self._error_response(request, HTTPError(405))
                resp.set_header("Allow", ", ".join(sorted(allowed)))
                return resp
            # /about/ -> /about
            if request.path != "/" and request.path.endswith("/"):
                stripped = request.path.rstrip("/")
                if any(r.match(stripped) is not None for r in self.routes):
                    qs = f"?{request.query_string}" if request.query_string else ""
                    return redirect(stripped + qs, 308)
            raise HTTPError(404)
        except HTTPError as err:
            return self._error_response(request, err)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            if self.debug:
                tb = escape(traceback.format_exc())
                body = (f"<!DOCTYPE html><title>Erreur</title><body style='font-family:monospace;padding:2rem'>"
                        f"<h1 style='color:#b91c1c'>{escape(type(exc).__name__)}: {escape(exc)}</h1>"
                        f"<pre style='background:#111;color:#eee;padding:1rem;overflow:auto'>{tb}</pre></body>")
                return Response(body, 500)
            return self._error_response(request, HTTPError(500))

    def handle(self, request: Request) -> Response:
        _local.request = request
        if self.base_path and (request.path == self.base_path or request.path.startswith(self.base_path + "/")):
            request.path = request.path[len(self.base_path):] or "/"
        try:
            response = self.dispatch(request)
            for hook in self._after:
                rv = self._call(hook, request, response=response)
                if isinstance(rv, Response):
                    response = rv
            if request._session is not None and request._session.modified:
                response.set_cookie(self.session_cookie, request._session.dump(self.get_secret_key()), max_age=30 * 86400)
            if request.method == "HEAD":
                response.body = b""
            return response
        finally:
            _local.request = None

    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        """WSGI entry point."""
        response = self.handle(Request(environ, self))
        start_response(response.status_line, response.headers)
        return response.iter_body()

    # -- tools ---------------------------------------------------------------
    def test_client(self) -> "TestClient":
        """Test client: ``app.test_client().get("/")``."""
        return TestClient(self)

    def run(self, host: str = "127.0.0.1", port: int = 8000, debug: bool = True,
            reload: Optional[bool] = None) -> None:
        """Start the development server. ``reload`` restarts it when a file changes."""
        from .server import run_server  # import local
        self.debug = debug
        run_server(self, host, port, reload=debug if reload is None else reload)

    def build(self, out_dir: str = "dist", extra_paths: Iterable[str] = ()) -> List[str]:
        """Optional static export: render every parameterless GET route + copy /static.

        Dynamic routes (``/user/<id>``) can be exported by listing the wanted
        URLs in ``extra_paths``.
        """
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir)
        client = self.test_client()
        paths = [r.path for r in self.routes if r.is_static and "GET" in r.methods] + list(extra_paths)
        written = []
        for path in dict.fromkeys(paths):
            resp = client.get(path)
            if resp.status != 200:
                continue
            ctype = resp.content_type
            if path == "/":
                target = "index.html"
            elif os.path.splitext(path)[1]:
                target = path.lstrip("/")
            elif "json" in ctype:
                target = path.lstrip("/") + ".json"
            else:
                target = path.strip("/") + "/index.html"
            full = os.path.join(out_dir, target)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as f:
                f.write(resp.data)
            written.append(full)
        if self.static_folder and os.path.isdir(self.static_folder):
            dest = os.path.join(out_dir, self.static_url.strip("/"))
            shutil.copytree(self.static_folder, dest, dirs_exist_ok=True)
        if 404 in self._error_handlers:
            with open(os.path.join(out_dir, "404.html"), "wb") as f:
                f.write(client.get("/__claide_404_page__").data)
        return written


class TestClient:
    """Send requests to the app without starting a server (for tests)."""

    def __init__(self, app: App) -> None:
        self.app = app
        self.cookies: Dict[str, str] = {}

    def request(self, method: str, path: str, *, data: Optional[dict] = None, json_data: Any = None,
                body: bytes = b"", headers: Optional[Dict[str, str]] = None) -> Response:
        import io
        from urllib.parse import urlencode, urlsplit

        parts = urlsplit(path)
        ctype = ""
        if json_data is not None:
            body, ctype = json.dumps(json_data).encode(), "application/json"
        elif data is not None:
            body, ctype = urlencode(data, doseq=True).encode(), "application/x-www-form-urlencoded"
        environ = {
            "REQUEST_METHOD": method.upper(),
            "PATH_INFO": parts.path.encode("utf-8").decode("latin-1"),
            "QUERY_STRING": parts.query,
            "SERVER_NAME": "testserver", "SERVER_PORT": "80", "HTTP_HOST": "testserver",
            "wsgi.url_scheme": "http", "wsgi.input": io.BytesIO(body),
            "CONTENT_LENGTH": str(len(body)), "REMOTE_ADDR": "127.0.0.1",
        }
        if ctype:
            environ["CONTENT_TYPE"] = ctype
        if self.cookies:
            environ["HTTP_COOKIE"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        for k, v in (headers or {}).items():
            key = k.upper().replace("-", "_")
            environ[key if key in ("CONTENT_TYPE", "CONTENT_LENGTH") else "HTTP_" + key] = v
        resp = self.app.handle(Request(environ, self.app))
        resp.body = resp.data  # consume generators
        for k, v in resp.headers:
            if k.lower() == "set-cookie":
                c = SimpleCookie()
                c.load(v)
                for name, morsel in c.items():
                    if morsel["max-age"] == "0":
                        self.cookies.pop(name, None)
                    else:
                        self.cookies[name] = morsel.value
        return resp

    def get(self, path: str, **kw: Any) -> Response:
        return self.request("GET", path, **kw)

    def post(self, path: str, **kw: Any) -> Response:
        return self.request("POST", path, **kw)

    def put(self, path: str, **kw: Any) -> Response:
        return self.request("PUT", path, **kw)

    def delete(self, path: str, **kw: Any) -> Response:
        return self.request("DELETE", path, **kw)


def generate_secret_key() -> str:
    return secrets.token_hex(32)


# Prevent pytest from collecting TestClient as a test class
TestClient.__test__ = False  # type: ignore[attr-defined]
