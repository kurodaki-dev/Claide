"""Construction de HTML en Python pur.

    >>> from claide import tags as t
    >>> str(t.div(t.h1("Salut"), class_="hero"))
    '<div class="hero"><h1>Salut</h1></div>'
"""

from __future__ import annotations

import html as _html
from typing import Any, Iterable, Iterator, List, Tuple

__all__ = ["Element", "Fragment", "Raw", "raw", "escape", "tags", "render_node", "iter_assets"]

#: Balises auto-fermantes (pas de contenu, pas de balise fermante).
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

#: Un "asset" est un tuple (type, contenu). Types possibles :
#:   "css"    -> lien vers une feuille de style (href)
#:   "style"  -> CSS inline (contenu d'une balise <style>)
#:   "js"     -> lien vers un script (src)
#:   "script" -> JavaScript inline
Asset = Tuple[str, str]


def escape(value: Any) -> str:
    """Échappe une valeur pour l'insérer dans du HTML."""
    return _html.escape(str(value), quote=True)


class Raw(str):
    """Chaîne HTML insérée telle quelle (non échappée)."""

    def __html__(self) -> str:
        return str(self)


def raw(value: str) -> Raw:
    """Marque une chaîne comme du HTML sûr, qui ne sera pas échappé."""
    return Raw(value)


def _attr_name(name: str) -> str:
    # class_ -> class, for_ -> for, data_user_id -> data-user-id
    name = name.rstrip("_")
    return name.replace("_", "-")


def _style_value(value: Any) -> str:
    if isinstance(value, dict):
        return "; ".join(f"{_attr_name(k)}: {v}" for k, v in value.items())
    return str(value)


def render_attrs(attrs: dict) -> str:
    parts = []
    for key, value in attrs.items():
        if value is None or value is False:
            continue
        name = key if "-" in key or ":" in key or "@" in key else _attr_name(key)
        if value is True:
            parts.append(f" {name}")
            continue
        if name == "style":
            value = _style_value(value)
        elif name == "class" and isinstance(value, (list, tuple, set)):
            value = " ".join(str(v) for v in value if v)
        parts.append(f' {name}="{escape(value)}"')
    return "".join(parts)


def _flatten(children: Iterable[Any]) -> Iterator[Any]:
    for child in children:
        if child is None or child is False or child is True:
            continue
        if isinstance(child, (list, tuple)) or (
            hasattr(child, "__iter__") and not isinstance(child, (str, bytes, dict)) and not hasattr(child, "__html__")
        ):
            yield from _flatten(child)
        else:
            yield child


def render_node(node: Any) -> str:
    """Transforme n'importe quel nœud (Element, UITemplate, str, nombre...) en HTML."""
    if node is None:
        return ""
    if hasattr(node, "__html__"):
        return node.__html__()
    return escape(node)


def iter_assets(node: Any) -> Iterator[Asset]:
    """Parcourt un nœud et renvoie tous les assets (CSS/JS) qu'il nécessite."""
    getter = getattr(node, "claide_assets", None)
    if getter is not None:
        yield from getter()


class Element:
    """Un élément HTML.

    Les attributs sont passés en mots-clés : ``class_`` devient ``class``,
    ``data_id`` devient ``data-id``. ``True`` produit un attribut booléen et
    ``None``/``False`` le supprime. ``style`` accepte un dict.
    """

    def __init__(self, tag: str | None, *children: Any, **attrs: Any) -> None:
        self.tag = tag
        self.children: List[Any] = list(_flatten(children))
        self.attrs: dict = attrs
        self._assets: List[Asset] = []

    # -- construction ------------------------------------------------------
    def add(self, *children: Any) -> "Element":
        """Ajoute des enfants et renvoie l'élément (chaînable)."""
        self.children.extend(_flatten(children))
        return self

    __iadd__ = lambda self, other: self.add(other)  # noqa: E731

    def __call__(self, *children: Any, **attrs: Any) -> "Element":
        """``div(class_="x")("contenu")`` : ajoute enfants et attributs."""
        self.attrs.update(attrs)
        return self.add(*children)

    def set(self, **attrs: Any) -> "Element":
        self.attrs.update(attrs)
        return self

    def add_class(self, *names: str) -> "Element":
        current = self.attrs.get("class_") or self.attrs.get("class") or ""
        if isinstance(current, (list, tuple)):
            current = " ".join(current)
        self.attrs.pop("class", None)
        self.attrs["class_"] = " ".join(filter(None, [current, *names]))
        return self

    def with_css(self, css: str) -> "Element":
        """Attache du CSS inline à cet élément (injecté dans le <head> de la page)."""
        self._assets.append(("style", css))
        return self

    def with_js(self, js: str) -> "Element":
        """Attache du JavaScript inline à cet élément (injecté en fin de <body>)."""
        self._assets.append(("script", js))
        return self

    def with_stylesheet(self, href: str) -> "Element":
        self._assets.append(("css", href))
        return self

    def with_script(self, src: str) -> "Element":
        self._assets.append(("js", src))
        return self

    # -- rendu -------------------------------------------------------------
    def claide_assets(self) -> Iterator[Asset]:
        yield from self._assets
        for child in self.children:
            yield from iter_assets(child)

    def render(self) -> str:
        inner = "".join(render_node(c) for c in self.children)
        if self.tag is None:
            return inner
        attrs = render_attrs(self.attrs)
        if self.tag in VOID_TAGS:
            return f"<{self.tag}{attrs}>"
        return f"<{self.tag}{attrs}>{inner}</{self.tag}>"

    def __html__(self) -> str:
        return self.render()

    __str__ = render

    def __repr__(self) -> str:
        return f"<Element {self.tag!r} children={len(self.children)}>"


class Fragment(Element):
    """Groupe d'éléments sans balise englobante."""

    def __init__(self, *children: Any) -> None:
        super().__init__(None, *children)


class _Tags:
    """Fabrique de balises : ``tags.div(...)``, ``tags.my_widget(...)`` -> ``<my-widget>``."""

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        tag = name.rstrip("_").replace("_", "-")

        def factory(*children: Any, **attrs: Any) -> Element:
            return Element(tag, *children, **attrs)

        factory.__name__ = name
        factory.__doc__ = f"Crée un élément <{tag}>."
        return factory

    def __call__(self, tag: str, *children: Any, **attrs: Any) -> Element:
        return Element(tag, *children, **attrs)


tags = _Tags()
