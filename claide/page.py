"""Une page HTML complète (<!DOCTYPE html> ... </html>)."""

from __future__ import annotations

import os
from typing import Any, Iterable, List, Optional

from .html import Asset, Element, escape, iter_assets, render_attrs, render_node

__all__ = ["Page"]


class Page:
    """Page HTML complète.

    Exemple ::

        page = Page("Accueil", description="Mon site")
        page.css("/static/style.css")
        page.js("/static/script.js")
        page.add(tags.h1("Bienvenue !"))
        html = page.render()
    """

    def __init__(
        self,
        title: str = "",
        *children: Any,
        lang: str = "fr",
        charset: str = "utf-8",
        description: Optional[str] = None,
        favicon: Optional[str] = None,
        viewport: str = "width=device-width, initial-scale=1",
        body_attrs: Optional[dict] = None,
        html_attrs: Optional[dict] = None,
    ) -> None:
        self.title = title
        self.lang = lang
        self.charset = charset
        self.description = description
        self.favicon = favicon
        self.viewport = viewport
        self.body = Element("body", *children, **(body_attrs or {}))
        self.html_attrs = html_attrs or {}
        self.head_extra: List[Any] = []
        self.metas: List[dict] = []
        self._assets: List[Asset] = []

    # -- contenu -------------------------------------------------------------
    def add(self, *children: Any) -> "Page":
        """Ajoute des éléments dans le <body>."""
        self.body.add(*children)
        return self

    def head(self, *elements: Any) -> "Page":
        """Ajoute des éléments bruts dans le <head>."""
        self.head_extra.extend(elements)
        return self

    def meta(self, **attrs: Any) -> "Page":
        """Ajoute une balise <meta>, ex. ``page.meta(property="og:title", content="...")``."""
        self.metas.append(attrs)
        return self

    # -- assets --------------------------------------------------------------
    def css(self, *hrefs: str) -> "Page":
        """Lie une ou plusieurs feuilles de style (``<link rel="stylesheet">``)."""
        self._assets.extend(("css", h) for h in hrefs)
        return self

    stylesheet = css

    def js(self, *srcs: str) -> "Page":
        """Lie un ou plusieurs scripts (``<script src defer>``)."""
        self._assets.extend(("js", s) for s in srcs)
        return self

    script_src = js

    def style(self, css: str) -> "Page":
        """Ajoute du CSS inline dans une balise <style>."""
        self._assets.append(("style", css))
        return self

    def script(self, code: str) -> "Page":
        """Ajoute du JavaScript inline en fin de <body>."""
        self._assets.append(("script", code))
        return self

    def style_file(self, path: str) -> "Page":
        """Lit un fichier .css local et l'intègre directement dans la page."""
        with open(path, encoding="utf-8") as f:
            return self.style(f.read())

    def script_file(self, path: str) -> "Page":
        """Lit un fichier .js local et l'intègre directement dans la page."""
        with open(path, encoding="utf-8") as f:
            return self.script(f.read())

    def use(self, *templates: Any) -> "Page":
        """Charge le CSS/JS de composants (ex. UITemplate) sans les afficher."""
        for t in templates:
            self._assets.extend(iter_assets(t))
        return self

    # -- rendu ---------------------------------------------------------------
    def collect_assets(self, extra: Iterable[Asset] = ()) -> List[Asset]:
        seen = set()
        result: List[Asset] = []
        for asset in [*extra, *self._assets, *iter_assets(self.body)]:
            if asset not in seen:
                seen.add(asset)
                result.append(asset)
        return result

    def render(self, extra_assets: Iterable[Asset] = ()) -> str:
        assets = self.collect_assets(extra_assets)
        head: List[str] = [
            f'<meta charset="{escape(self.charset)}">',
            f'<meta name="viewport" content="{escape(self.viewport)}">',
            f"<title>{escape(self.title)}</title>",
        ]
        if self.description:
            head.append(f'<meta name="description" content="{escape(self.description)}">')
        if self.favicon:
            head.append(f'<link rel="icon" href="{escape(self.favicon)}">')
        for m in self.metas:
            head.append(f"<meta{render_attrs(m)}>")
        for kind, value in assets:
            if kind == "css":
                head.append(f'<link rel="stylesheet" href="{escape(value)}">')
            elif kind == "style":
                head.append(f"<style>\n{value}\n</style>")
            elif kind == "js-head":
                head.append(f'<script src="{escape(value)}"></script>')
        head.extend(render_node(h) for h in self.head_extra)

        tail: List[str] = []
        for kind, value in assets:
            if kind == "js":
                tail.append(f'<script src="{escape(value)}"></script>')
            elif kind == "module":
                tail.append(f'<script type="module" src="{escape(value)}"></script>')
            elif kind == "script":
                tail.append(f"<script>\n{value}\n</script>")

        body_attrs = render_attrs(self.body.attrs)
        body_inner = "".join(render_node(c) for c in self.body.children)
        html_attrs = render_attrs({"lang": self.lang, **self.html_attrs})
        nl = "\n"
        return (
            f"<!DOCTYPE html>\n<html{html_attrs}>\n<head>\n{nl.join(head)}\n</head>\n"
            f"<body{body_attrs}>\n{body_inner}\n{nl.join(tail)}\n</body>\n</html>\n"
        )

    def __html__(self) -> str:
        return self.render()

    __str__ = render

    def save(self, path: str) -> str:
        """Écrit la page dans un fichier .html et renvoie le chemin."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.render())
        return path

