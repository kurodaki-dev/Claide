"""Claide: build complete websites in Python, from A to Z.

The shortest version::

    from claide import *

    @route("/")
    def home():
        return h1("Hello!"), p("Welcome to my site.")

    run()

See https://kurodaki-dev.github.io/Claide/
"""

from .app import (
    App, HTTPError, Request, Response, Router, UploadedFile, abort, redirect, request, send_file,
)
from .html import Element, Fragment, Raw, escape, raw, tags
from .markdown import md
from .page import Page
from .quick import default_app, delete, error, get, layout, post, put, route, run
from .uitemplate import CATEGORIES, UITemplate, UITemplateError, builtin_templates

# Also allows "from claide import uitemplate" then uitemplate.UITemplate(...)
from . import components, uitemplate  # noqa: E402

__version__ = "0.3.0"

#: Short alias: ``ui("https://uiverse.io/author/name")``.
ui = UITemplate

# HTML tags usable directly: h1("Title"), p("Text"), div(...), a("Link", href="/")...
# Tags whose name would hide a Python builtin or a common module end with "_":
# input_(...), time_(...), del_(...). Tags whose name is a very common variable
# name (i, b, s, q, data, output, source...) are only available as tags.<name>().
_TAG_NAMES = """
a abbr address article aside audio blockquote br button canvas caption code
datalist dd details dialog div dl dt em embed fieldset figcaption figure footer form
h1 h2 h3 h4 h5 h6 header hgroup hr iframe img ins kbd label legend li main mark nav
noscript ol optgroup option p picture pre progress section select small
span strong sub summary sup svg table tbody td textarea tfoot th thead tr ul video
""".split()
_RENAMED = {"input_": "input", "time_": "time", "del_": "del"}

for _name in _TAG_NAMES:
    globals()[_name] = getattr(tags, _name)
for _alias in _RENAMED:
    globals()[_alias] = getattr(tags, _alias)

__all__ = [
    # build a site quickly
    "route", "get", "post", "put", "delete", "run", "layout", "error", "default_app",
    "request", "redirect", "abort",
    # pages and content
    "Page", "Element", "Fragment", "Raw", "raw", "escape", "tags", "md",
    # components
    "ui", "UITemplate", "UITemplateError", "CATEGORIES", "builtin_templates", "components", "uitemplate",
    # full control
    "App", "Router", "Request", "Response", "UploadedFile", "HTTPError", "send_file",
    "__version__",
    *_TAG_NAMES, *_RENAMED,
]
