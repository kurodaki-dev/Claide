"""Claide — crée des sites web complets en Python, de A à Z.

    from claide import App, Page, UITemplate, tags as t

Voir https://github.com/kurodaki-dev/Claide
"""

from .app import (
    App, HTTPError, Request, Response, Router, UploadedFile, abort, redirect, send_file,
)
from .html import Element, Fragment, Raw, escape, raw, tags
from .page import Page
from .uitemplate import CATEGORIES, UITemplate, UITemplateError, builtin_templates

# Permet aussi "from claide import uitemplate" puis uitemplate.UITemplate(...)
from . import components, uitemplate  # noqa: E402

__version__ = "0.1.0"

__all__ = [
    "App", "Router", "Request", "Response", "UploadedFile", "HTTPError",
    "abort", "redirect", "send_file",
    "Element", "Fragment", "Raw", "escape", "raw", "tags",
    "Page", "UITemplate", "UITemplateError", "CATEGORIES", "builtin_templates",
    "components", "uitemplate", "__version__",
]
