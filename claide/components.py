"""Blocs de mise en page prêts à l'emploi (avec leur CSS intégré).

    from claide.components import Navbar, Hero, Section, Grid, Card, Footer, Form, Field
"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, Tuple, Union

from .html import Element

__all__ = [
    "BASE_CSS", "Container", "Navbar", "Hero", "Section", "Grid", "Card",
    "Footer", "Form", "Field", "Button", "Alert",
]

BASE_CSS = """:root {
  --cl-primary: #6366f1; --cl-text: #111827; --cl-muted: #6b7280;
  --cl-bg: #ffffff; --cl-surface: #f9fafb; --cl-border: #e5e7eb; --cl-radius: 12px;
}
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  color: var(--cl-text); background: var(--cl-bg); line-height: 1.6; }
img { max-width: 100%; }
.cl-container { width: min(1100px, 100% - 2rem); margin-inline: auto; }
.cl-nav { position: sticky; top: 0; z-index: 10; background: color-mix(in srgb, var(--cl-bg) 85%, transparent);
  backdrop-filter: blur(8px); border-bottom: 1px solid var(--cl-border); }
.cl-nav .cl-container { display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  min-height: 64px; flex-wrap: wrap; }
.cl-brand { font-weight: 800; font-size: 1.2rem; color: inherit; text-decoration: none; }
.cl-nav ul { display: flex; gap: 1.25rem; list-style: none; margin: 0; padding: 0; flex-wrap: wrap; }
.cl-nav a { color: inherit; text-decoration: none; opacity: .8; }
.cl-nav a:hover, .cl-nav a[aria-current] { opacity: 1; color: var(--cl-primary); }
.cl-hero { padding: clamp(3rem, 10vw, 7rem) 0; text-align: center; }
.cl-hero h1 { font-size: clamp(2rem, 6vw, 3.5rem); line-height: 1.1; margin: 0 0 1rem; }
.cl-hero p { font-size: 1.2rem; color: var(--cl-muted); max-width: 640px; margin: 0 auto 2rem; }
.cl-hero .cl-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
.cl-section { padding: 4rem 0; }
.cl-section > .cl-container > h2 { font-size: 2rem; margin: 0 0 1.5rem; }
.cl-section.cl-alt { background: var(--cl-surface); }
.cl-grid { display: grid; gap: 1.5rem; grid-template-columns: repeat(auto-fit, minmax(min(var(--cl-min, 250px), 100%), 1fr)); }
.cl-card-box { background: var(--cl-bg); border: 1px solid var(--cl-border); border-radius: var(--cl-radius);
  padding: 1.5rem; overflow: hidden; }
.cl-card-box > img { display: block; margin: -1.5rem -1.5rem 1rem; width: calc(100% + 3rem); max-width: none;
  aspect-ratio: 16/9; object-fit: cover; }
.cl-card-box h3 { margin: 0 0 .5rem; }
.cl-card-box h3 a { color: inherit; text-decoration: none; }
.cl-card-box h3 a:hover { color: var(--cl-primary); }
.cl-card-box p { margin: 0; color: var(--cl-muted); }
.cl-btn { display: inline-block; padding: .7em 1.4em; border-radius: 10px; border: 1px solid var(--cl-primary);
  background: var(--cl-primary); color: #fff; font: inherit; font-weight: 600; text-decoration: none; cursor: pointer;
  transition: filter .2s, transform .1s; }
.cl-btn:hover { filter: brightness(1.1); }
.cl-btn:active { transform: scale(.97); }
.cl-btn.cl-outline { background: transparent; color: var(--cl-primary); }
.cl-form { display: grid; gap: 1rem; max-width: 520px; }
.cl-field { display: grid; gap: .35rem; }
.cl-field label { font-weight: 600; font-size: .95rem; }
.cl-field input, .cl-field textarea, .cl-field select { font: inherit; padding: .65em .8em;
  border: 1px solid var(--cl-border); border-radius: 8px; background: var(--cl-bg); color: inherit; }
.cl-field input:focus, .cl-field textarea:focus, .cl-field select:focus {
  outline: 2px solid var(--cl-primary); outline-offset: 1px; }
.cl-alert { padding: 1rem 1.25rem; border-radius: 10px; border: 1px solid; margin: 1rem 0; }
.cl-alert-info { background: #eef2ff; border-color: #c7d2fe; color: #3730a3; }
.cl-alert-success { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
.cl-alert-error { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
.cl-footer { padding: 2rem 0; border-top: 1px solid var(--cl-border); color: var(--cl-muted); text-align: center; }
"""

Link = Union[Tuple[str, str], Sequence[str]]


def _el(tag: str, *children: Any, **attrs: Any) -> Element:
    return Element(tag, *children, **attrs).with_css(BASE_CSS)


def Container(*children: Any, **attrs: Any) -> Element:
    return _el("div", *children, **attrs).add_class("cl-container")


def Navbar(brand: Any = "Mon site", links: Iterable[Link] = (), brand_href: str = "/",
           current: Optional[str] = None, **attrs: Any) -> Element:
    """Barre de navigation. ``links=[("Accueil", "/"), ("Contact", "/contact")]``."""
    items = [
        Element("li", Element("a", label, href=href, aria_current="page" if href == current else None))
        for label, href in links
    ]
    return _el("nav", Container(Element("a", brand, href=brand_href, class_="cl-brand"),
                                Element("ul", *items)), **attrs).add_class("cl-nav")


def Button(label: Any, href: Optional[str] = None, outline: bool = False, **attrs: Any) -> Element:
    """Bouton simple (lien si ``href`` est donné)."""
    cls = "cl-btn cl-outline" if outline else "cl-btn"
    if href is not None:
        return _el("a", label, href=href, **attrs).add_class(cls)
    attrs.setdefault("type", "button")
    return _el("button", label, **attrs).add_class(cls)


def Hero(title: Any, subtitle: Any = None, *actions: Any, **attrs: Any) -> Element:
    """Grande bannière d'accueil. ``actions`` : boutons, UITemplate..."""
    return _el("header", Container(
        Element("h1", title),
        Element("p", subtitle) if subtitle else None,
        Element("div", *actions, class_="cl-actions") if actions else None,
    ), **attrs).add_class("cl-hero")


def Section(*children: Any, title: Any = None, alt: bool = False, id: Optional[str] = None, **attrs: Any) -> Element:  # noqa: A002
    el = _el("section", Container(Element("h2", title) if title else None, *children), id=id, **attrs)
    return el.add_class("cl-section", "cl-alt" if alt else "")


def Grid(*children: Any, min_width: str = "250px", **attrs: Any) -> Element:
    """Grille responsive : les colonnes s'adaptent à la largeur de l'écran."""
    style = attrs.pop("style", "")
    return _el("div", *children, style=f"--cl-min:{min_width};{style}", **attrs).add_class("cl-grid")


def Card(title: Any = None, *children: Any, image: Optional[str] = None, href: Optional[str] = None,
         **attrs: Any) -> Element:
    body = [
        Element("img", src=image, alt="", loading="lazy") if image else None,
        Element("h3", Element("a", title, href=href) if href else title) if title else None,
        *[Element("p", c) if isinstance(c, str) else c for c in children],
    ]
    return _el("article", *body, **attrs).add_class("cl-card-box")


def Footer(*children: Any, **attrs: Any) -> Element:
    return _el("footer", Container(*children), **attrs).add_class("cl-footer")


def Alert(message: Any, kind: str = "info", **attrs: Any) -> Element:
    """Message : ``kind`` = "info", "success" ou "error"."""
    return _el("div", message, role="alert", **attrs).add_class("cl-alert", f"cl-alert-{kind}")


def Field(label: str, name: str, type: str = "text", value: Any = None, required: bool = False,  # noqa: A002
          options: Optional[Iterable[Any]] = None, **attrs: Any) -> Element:
    """Champ de formulaire avec son label. ``type`` peut être "textarea" ou "select"."""
    fid = attrs.pop("id", f"f-{name}")
    if type == "textarea":
        control = Element("textarea", value or "", name=name, id=fid, required=required, rows=attrs.pop("rows", 5), **attrs)
    elif type == "select":
        opts = []
        for o in options or ():
            val, text = o if isinstance(o, (tuple, list)) else (o, o)
            opts.append(Element("option", text, value=val, selected=(str(val) == str(value)) if value is not None else None))
        control = Element("select", *opts, name=name, id=fid, required=required, **attrs)
    else:
        control = Element("input", type=type, name=name, id=fid, value=value, required=required, **attrs)
    return _el("div", Element("label", label, for_=fid), control).add_class("cl-field")


def Form(*children: Any, action: str = "", method: str = "post", submit: Optional[str] = "Envoyer",
         upload: bool = False, **attrs: Any) -> Element:
    """Formulaire. ``upload=True`` pour permettre l'envoi de fichiers."""
    if upload:
        attrs["enctype"] = "multipart/form-data"
    return _el("form", *children, Button(submit, type="submit") if submit else None,
               action=action, method=method, **attrs).add_class("cl-form")
