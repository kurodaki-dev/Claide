"""Shortcuts to build a site without creating an ``App`` yourself.

    from claide import *

    @route("/")
    def home():
        return h1("Hello!"), p("Welcome.")

    run()

They all use one application, created on first use with the clean default
theme. Access it with ``claide.default_app()`` when you need more control.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Callable, Iterable, Optional

from .app import App

__all__ = ["default_app", "route", "get", "post", "put", "delete", "run", "layout", "error"]

_app: Optional[App] = None


def default_app(module: Optional[str] = None, root: Optional[str] = None) -> App:
    """The application used by ``route``, ``get``, ``post`` and ``run``.

    It is created on first use, next to the file that declares the first
    route (that is where its ``static/`` folder is looked for).
    """
    global _app
    if _app is None:
        _app = App(module or "__main__", root=root, theme=True)
    return _app


def _root_of(func: Callable) -> Optional[str]:
    filename = getattr(getattr(func, "__code__", None), "co_filename", "")
    return os.path.dirname(os.path.abspath(filename)) if filename and os.path.isfile(filename) else None


def _register(path: str, methods: Iterable[str]) -> Callable:
    def decorator(func: Callable) -> Callable:
        return default_app(func.__module__, _root_of(func)).route(path, methods)(func)
    return decorator


def route(path: str, methods: Iterable[str] = ("GET", "POST")) -> Callable:
    """Register a page. Accepts GET and POST, so forms work without extra setup."""
    return _register(path, methods)


def get(path: str) -> Callable:
    """Register a route that only answers GET requests (pages, JSON APIs)."""
    return _register(path, ("GET",))


def post(path: str) -> Callable:
    """Register a route that only answers POST requests (forms, API calls)."""
    return _register(path, ("POST",))


def put(path: str) -> Callable:
    """Register a route that only answers PUT requests."""
    return _register(path, ("PUT",))


def delete(path: str) -> Callable:
    """Register a route that only answers DELETE requests."""
    return _register(path, ("DELETE",))


def layout(func: Callable) -> Callable:
    """Function applied to every page (navbar, footer...). See ``App.layout``."""
    return default_app(func.__module__, _root_of(func)).layout(func)


def error(status: int) -> Callable:
    """Custom page for an error code: ``@error(404)``."""
    def decorator(func: Callable) -> Callable:
        return default_app(func.__module__, _root_of(func)).errorhandler(status)(func)
    return decorator


def run(host: str = "127.0.0.1", port: int = 8000, **kwargs: Any) -> App:
    """Start the site on http://127.0.0.1:8000 (reloads when you save a file).

    The server only starts when the file is executed (``python app.py``).
    When the file is imported (by ``claide run``, gunicorn, tests...),
    ``run()`` does nothing, so it can stay at the end of your file.
    Returns the application, for ``app = run()``.
    """
    caller_globals = sys._getframe(1).f_globals
    caller = caller_globals.get("__name__")
    filename = caller_globals.get("__file__")
    root = os.path.dirname(os.path.abspath(filename)) if filename else None
    app = default_app(caller if caller != "__main__" else None, root)
    if caller == "__main__":
        app.run(host, port, **kwargs)
    return app
