"""Ready-to-use UI components, imported from Uiverse.io / cssbuttons.io.

cssbuttons.io redirects to https://uiverse.io/buttons. Every element published
on Uiverse is archived (MIT license) in the official GitHub repository
``uiverse-io/galaxy``: that is where Claide fetches them from.

Example ::

    from claide import UITemplate

    # With the "author/name" id visible in the Uiverse URL
    button = UITemplate("0x-Sarthak/hungry-penguin-30")

    # ... or straight from the URL copied from your browser
    button = UITemplate("https://uiverse.io/0x-Sarthak/hungry-penguin-30")

    # ... or by pasting the HTML/CSS code yourself
    button = UITemplate(html="<button class='btn'>OK</button>", css=".btn{...}")

    page.add(button.text("Contact Us", "Write me").attrs(onclick="hello()"))

The component's CSS is automatically injected into the page <head>.
"""

from __future__ import annotations

import copy
import hashlib
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .html import Asset, escape, render_attrs

__all__ = ["UITemplate", "UITemplateError", "CATEGORIES", "builtin_templates"]

GALAXY_RAW = "https://raw.githubusercontent.com/uiverse-io/galaxy/main"
TAILWIND_CDN = "https://cdn.tailwindcss.com"

#: Folders of the uiverse-io/galaxy repository (= categories on uiverse.io).
CATEGORIES = [
    "Buttons", "Cards", "Checkboxes", "Forms", "Inputs", "loaders",
    "Notifications", "Patterns", "Radio-buttons", "Toggle-switches", "Tooltips",
]

_CATEGORY_ALIASES = {c.lower().replace("-", ""): c for c in CATEGORIES}
_CATEGORY_ALIASES.update({
    "button": "Buttons", "card": "Cards", "checkbox": "Checkboxes", "form": "Forms",
    "input": "Inputs", "loader": "loaders", "notification": "Notifications",
    "pattern": "Patterns", "radio": "Radio-buttons", "radiobutton": "Radio-buttons",
    "toggle": "Toggle-switches", "switch": "Toggle-switches", "switches": "Toggle-switches",
    "toggleswitch": "Toggle-switches", "tooltip": "Tooltips",
})

_STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
_SCRIPT_RE = re.compile(r"<script[^>]*>(.*?)</script>", re.S | re.I)
_CREDIT_RE = re.compile(r"From Uiverse\.io by\s+([^\s]+)(?:\s*-\s*Tags:\s*([^*>]*?))?\s*(?:\*/|-->)", re.I)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_CLASS_ATTR_RE = re.compile(r'(\bclass\s*=\s*)(["\'])(.*?)\2', re.S | re.I)
_TAILWIND_HINT_RE = re.compile(
    r"\b(?:flex|grid|hidden|block|relative|absolute|rounded(?:-\w+)?|shadow(?:-\w+)?|"
    r"(?:bg|text|p[xytrbl]?|m[xytrbl]?|w|h|gap|border|font|items|justify)-[\w\[\]#./%-]+)\b"
)


class UITemplateError(Exception):
    """Error while loading a Uiverse component."""


def _cache_dir() -> str:
    base = os.environ.get("CLAIDE_CACHE_DIR") or os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache"), "claide"
    )
    path = os.path.join(base, "uiverse")
    os.makedirs(path, exist_ok=True)
    return path


def _normalize_category(category: Optional[str]) -> Optional[str]:
    if not category:
        return None
    key = category.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]
    raise UITemplateError(f"Unknown category: {category!r}. Available: {', '.join(CATEGORIES)}")


def parse_uiverse_id(ref: str) -> Tuple[str, str]:
    """``"author/name"``, ``"author_name"`` or a uiverse.io URL -> (author, name)."""
    ref = ref.strip()
    ref = re.sub(r"^https?://(www\.)?(uiverse\.io|cssbuttons\.io)/", "", ref)
    ref = ref.split("?")[0].split("#")[0].strip("/")
    if ref.endswith(".html"):
        ref = ref[:-5].rsplit("/", 1)[-1]
    if "/" in ref:
        author, name = ref.split("/", 1)
        # Also accept the repository path form "Buttons/author_name".
        if "/" in name:
            author, name = name.split("/", 1)
        elif "_" in name and author.lower().replace("-", "") in _CATEGORY_ALIASES:
            author, name = name.split("_", 1)
        return author, name
    if "_" in ref:
        author, name = ref.split("_", 1)
        return author, name
    raise UITemplateError(
        f"Invalid Uiverse id: {ref!r}. Use 'author/name' or the full URL, "
        "e.g. 'https://uiverse.io/0x-Sarthak/hungry-penguin-30'."
    )


def _download(url: str, timeout: float) -> Optional[str]:
    req = urllib.request.Request(url, headers={"User-Agent": "claide-python"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise UITemplateError(f"HTTP error {exc.code} while downloading {url}") from exc
    except urllib.error.URLError as exc:
        raise UITemplateError(f"Could not reach GitHub ({exc.reason}). Check your connection.") from exc


def fetch_uiverse_source(author: str, name: str, category: Optional[str] = None,
                         use_cache: bool = True, timeout: float = 10.0) -> Tuple[str, str]:
    """Download a component source file. Returns (category, source)."""
    filename = f"{author}_{name}.html"
    cache = _cache_dir()
    if use_cache:
        for cat in ([category] if category else CATEGORIES):
            cached = os.path.join(cache, cat, filename)
            if os.path.exists(cached):
                with open(cached, encoding="utf-8") as f:
                    return cat, f.read()

    order = [category] + [c for c in CATEGORIES if c != category] if category else list(CATEGORIES)
    for cat in order:
        source = _download(f"{GALAXY_RAW}/{cat}/{filename}", timeout)
        if source is not None:
            os.makedirs(os.path.join(cache, cat), exist_ok=True)
            with open(os.path.join(cache, cat, filename), "w", encoding="utf-8") as f:
                f.write(source)
            return cat, source
    raise UITemplateError(
        f"Component not found: {author}/{name}. Check the URL on uiverse.io "
        "(very recent elements can take a while to be archived)."
    )


def split_source(source: str) -> Tuple[str, str, str]:
    """Split a Uiverse file into (html, css, js)."""
    css = "\n".join(m.strip() for m in _STYLE_RE.findall(source))
    js = "\n".join(m.strip() for m in _SCRIPT_RE.findall(source))
    html = _SCRIPT_RE.sub("", _STYLE_RE.sub("", source))
    html = _HTML_COMMENT_RE.sub("", html).strip()
    return html, css, js


_AT_GROUP = ("@media", "@supports", "@container", "@layer", "@document", "@scope")
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)


def _matching_brace(css: str, start: int) -> int:
    """Index of the ``}`` closing the ``{`` at ``start`` (ignores strings and comments)."""
    depth, i, quote = 0, start, ""
    while i < len(css):
        ch = css[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = ""
        elif css.startswith("/*", i):
            end = css.find("*/", i + 2)
            i = len(css) if end == -1 else end + 1
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(css) - 1


def _split_selectors(prelude: str) -> List[str]:
    parts, depth, cur = [], 0, ""
    for ch in prelude:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def _scope_selector(sel: str, scope: str) -> str:
    m = re.match(r"(:root|html|body)(?![\w-])", sel)
    if m:
        rest = sel[m.end():]
        return f".{scope}{rest}"
    return f".{scope} {sel}"


def _scope_rules(css: str, scope: str, keyframes: Dict[str, str]) -> str:
    out: List[str] = []
    i = 0
    while i < len(css):
        brace = css.find("{", i)
        semi = css.find(";", i)
        if brace == -1:
            out.append(css[i:])
            break
        prelude = css[i:brace]
        lead = re.match(r"(\s|/\*.*?\*/)*", prelude, re.S)
        lead_text = lead.group(0) if lead else ""
        head = prelude[len(lead_text):]
        if head.startswith("@") and semi != -1 and semi < brace:
            out.append(css[i:semi + 1])  # @import ...; @charset ...;
            i = semi + 1
            continue
        end = _matching_brace(css, brace)
        body = css[brace + 1:end]
        head_clean = _COMMENT_RE.sub("", head).strip()
        if head_clean.startswith(_AT_GROUP):
            out.append(f"{lead_text}{head}{{{_scope_rules(body, scope, keyframes)}}}")
        elif re.match(r"@(-\w+-)?keyframes\b", head_clean):
            name = head_clean.split(None, 1)[1].strip() if " " in head_clean else ""
            new_head = head.replace(name, keyframes.get(name, name), 1) if name else head
            out.append(f"{lead_text}{new_head}{{{body}}}")
        elif head_clean.startswith("@"):
            out.append(css[i:end + 1])  # @font-face, @page... copied as is
        else:
            selectors = ", ".join(_scope_selector(sel, scope) for sel in _split_selectors(head_clean))
            out.append(f"{lead_text}{selectors} {{{body}}}")
        i = end + 1
    return "".join(out)


def scope_css(css: str, scope: str) -> str:
    """Prefix every selector of ``css`` with ``.scope`` and rename its @keyframes."""
    names = re.findall(r"@(?:-\w+-)?keyframes\s+([\w-]+)", css)
    keyframes = {n: f"{scope}-{n}" for n in names}
    scoped = _scope_rules(css, scope, keyframes)
    if keyframes:
        pattern = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, keyframes)) + r")(?![\w-])")

        def fix_decl(m: "re.Match[str]") -> str:
            return m.group(1) + pattern.sub(lambda k: keyframes[k.group(1)], m.group(2))

        scoped = re.sub(r"(animation(?:-name)?\s*:)([^;}]*)", fix_decl, scoped)
    return scoped


class UITemplate:
    """A reusable UI component (HTML + CSS [+ JS]).

    ``UITemplate("author/name")`` downloads the component from Uiverse.
    ``UITemplate(html=..., css=...)`` creates a component from your own code.
    ``UITemplate.builtin("glow")`` uses a component bundled with Claide (offline).

    A ``UITemplate`` can be added directly to a ``Page`` or an ``Element``:
    its CSS is automatically injected into the <head>.
    """

    def __init__(
        self,
        ref: Optional[str] = None,
        *,
        html: Optional[str] = None,
        css: str = "",
        js: str = "",
        category: Optional[str] = None,
        scoped: bool = False,
        tailwind: Optional[bool] = None,
        use_cache: bool = True,
        timeout: float = 10.0,
    ) -> None:
        self.author: Optional[str] = None
        self.name: Optional[str] = None
        self.category: Optional[str] = _normalize_category(category)
        self.tags: List[str] = []
        self.scope: Optional[str] = None  # wrapper class set by .scoped()

        if ref is not None:
            if html is not None:
                raise UITemplateError("Pass either a Uiverse id or html=..., not both.")
            self.author, self.name = parse_uiverse_id(ref)
            self.category, source = fetch_uiverse_source(
                self.author, self.name, self.category, use_cache=use_cache, timeout=timeout
            )
            credit = _CREDIT_RE.search(source)
            if credit and credit.group(2):
                self.tags = [t.strip() for t in credit.group(2).split(",") if t.strip()]
            html, file_css, file_js = split_source(source)
            css = (file_css + "\n" + css).strip()
            js = (file_js + "\n" + js).strip()
        elif html is None:
            raise UITemplateError("UITemplate needs a Uiverse id or html=...")

        self.html: str = html.strip()
        self.css: str = css.strip()
        self.js: str = js.strip()
        if tailwind is None:
            # Uiverse components without <style> are written with Tailwind CSS.
            tailwind = not self.css and bool(_TAILWIND_HINT_RE.search(" ".join(self.classes())))
        self.tailwind: bool = tailwind
        if scoped:
            self._scope_in_place()

    # -- alternative constructors -------------------------------------------
    @classmethod
    def uiverse(cls, ref: str, **kwargs: Any) -> "UITemplate":
        """Explicit alias: ``UITemplate.uiverse("author/name")``."""
        return cls(ref, **kwargs)

    @classmethod
    def from_source(cls, source: str, **kwargs: Any) -> "UITemplate":
        """Create a component from an HTML block that may contain <style>/<script>."""
        html, css, js = split_source(source)
        return cls(html=html, css=css, js=js, **kwargs)

    @classmethod
    def from_file(cls, path: str, **kwargs: Any) -> "UITemplate":
        """Load a component from an .html file (HTML + <style> + <script>)."""
        with open(path, encoding="utf-8") as f:
            return cls.from_source(f.read(), **kwargs)

    @classmethod
    def builtin(cls, name: str, label: Optional[str] = None) -> "UITemplate":
        """Component bundled with Claide (works offline). See ``builtin_templates()``."""
        try:
            data = _BUILTINS[name]
        except KeyError:
            raise UITemplateError(
                f"Unknown built-in component: {name!r}. Available: {', '.join(_BUILTINS)}"
            ) from None
        tpl = cls(html=data["html"], css=data["css"], js=data.get("js", ""))
        tpl.name = name
        tpl.author = "claide"
        if label is not None:
            tpl = tpl.text(data.get("label", "Button"), label)
        return tpl

    # -- customization -----------------------------------------------------
    def copy(self) -> "UITemplate":
        return copy.copy(self)

    def text(self, old: str, new: Optional[str] = None) -> "UITemplate":
        """Replace visible text: ``.text("Contact Us", "Write me")``.

        With a single argument, replaces the first non-empty text node.
        The new text is escaped (use ``.replace`` to insert HTML).
        """
        tpl = self.copy()
        if new is None:
            new = old
            match = re.search(r">\s*([^<>\s][^<>]*?)\s*<", tpl.html)
            if not match:
                raise UITemplateError("No text found in this component.")
            start, end = match.span(1)
            tpl.html = tpl.html[:start] + escape(new) + tpl.html[end:]
            return tpl
        if old not in tpl.html:
            raise UITemplateError(f"Text {old!r} not found in the component.")
        tpl.html = tpl.html.replace(old, escape(new))
        return tpl

    def replace(self, old: str, new: str, css: bool = False) -> "UITemplate":
        """Raw replacement in the HTML (or in the CSS when ``css=True``)."""
        tpl = self.copy()
        if css:
            tpl.css = tpl.css.replace(old, new)
        else:
            tpl.html = tpl.html.replace(old, new)
        return tpl

    def attrs(self, **attrs: Any) -> "UITemplate":
        """Add attributes to the root element: ``.attrs(id="send", onclick="go()")``.

        ``class_`` is appended to the existing classes.
        """
        tpl = self.copy()
        match = re.search(r"<([a-zA-Z][\w-]*)([^>]*?)(/?)>", tpl.html)
        if not match:
            raise UITemplateError("Could not find the root element of the component.")
        tag, existing, selfclose = match.groups()
        extra_class = attrs.pop("class_", None) or attrs.pop("class", None)
        if extra_class:
            cm = _CLASS_ATTR_RE.search(existing)
            if cm:
                existing = existing[: cm.start(3)] + cm.group(3) + " " + escape(extra_class) + existing[cm.end(3):]
            else:
                existing += f' class="{escape(extra_class)}"'
        new_tag = f"<{tag}{existing}{render_attrs(attrs)}{selfclose}>"
        tpl.html = tpl.html[: match.start()] + new_tag + tpl.html[match.end():]
        return tpl

    def link(self, href: str, **attrs: Any) -> "UITemplate":
        """Wrap the component in an <a href=...> link."""
        tpl = self.copy()
        attrs.setdefault("style", "text-decoration:none;display:inline-block")
        tpl.html = f'<a href="{escape(href)}"{render_attrs(attrs)}>{tpl.html}</a>'
        return tpl

    def add_css(self, css: str) -> "UITemplate":
        """Add CSS to the component (to override colors, etc.)."""
        tpl = self.copy()
        if tpl.scope:
            css = scope_css(css, tpl.scope)
        tpl.css = (tpl.css + "\n" + css).strip()
        return tpl

    def add_js(self, js: str) -> "UITemplate":
        tpl = self.copy()
        tpl.js = (tpl.js + "\n" + js).strip()
        return tpl

    # -- CSS class isolation -----------------------------------------------
    def classes(self) -> List[str]:
        """List the CSS classes used in the component HTML."""
        found: List[str] = []
        for m in _CLASS_ATTR_RE.finditer(self.html):
            for c in m.group(3).split():
                if c not in found:
                    found.append(c)
        return found

    def prefix(self, prefix: str) -> "UITemplate":
        """Prefix every CSS class (HTML + CSS) to avoid conflicts."""
        tpl = self.copy()
        tpl._rename_classes({c: prefix + c for c in tpl.classes()})
        return tpl

    def scoped(self) -> "UITemplate":
        """Isolate the component's CSS from the rest of the page.

        The component is rendered inside an invisible wrapper
        (``display: contents``) with a unique class, every CSS selector is
        prefixed with that class and ``@keyframes`` names are renamed. Rules
        such as ``button { ... }`` or ``#timer { ... }`` then only apply to
        this component, and two components that both use ``.button`` no
        longer conflict.
        """
        tpl = self.copy()
        tpl._scope_in_place()
        return tpl

    def _scope_in_place(self) -> None:
        if self.scope or self.tailwind:
            return
        digest = hashlib.sha1((self.html + self.css + self.js).encode("utf-8")).hexdigest()[:6]
        self.scope = f"u{digest}"
        self.css = scope_css(self.css, self.scope)

    def _rename_classes(self, mapping: Dict[str, str]) -> None:
        if not mapping or self.tailwind:
            return

        def fix_attr(m: "re.Match[str]") -> str:
            names = [mapping.get(c, c) for c in m.group(3).split()]
            return f"{m.group(1)}{m.group(2)}{' '.join(names)}{m.group(2)}"

        self.html = _CLASS_ATTR_RE.sub(fix_attr, self.html)
        # Replace longest names first so ".btn" does not affect ".btn-icon".
        for old in sorted(mapping, key=len, reverse=True):
            pattern = re.compile(r"\." + re.escape(old) + r"(?![\w-])")
            self.css = pattern.sub("." + mapping[old], self.css)
            if self.js:
                self.js = re.sub(r"(['\"`.])" + re.escape(old) + r"(?![\w-])",
                                 lambda m, new=mapping[old]: m.group(1) + new, self.js)

    # -- render ---------------------------------------------------------------
    @property
    def credit(self) -> str:
        if self.author and self.author != "claide":
            return f"From Uiverse.io by {self.author} (MIT)"
        return ""

    def claide_assets(self) -> Iterator[Asset]:
        if self.tailwind:
            yield ("js-head", TAILWIND_CDN)
        if self.css:
            header = f"/* {self.credit} */\n" if self.credit and "Uiverse.io" not in self.css else ""
            yield ("style", header + self.css)
        if self.js:
            yield ("script", self.js)

    def __html__(self) -> str:
        if self.scope:
            return f'<div class="{self.scope}" style="display:contents">{self.html}</div>'
        return self.html

    def render(self) -> str:
        return self.__html__()

    __str__ = render

    def __repr__(self) -> str:
        who = f"{self.author}/{self.name}" if self.author else "custom"
        return f"<UITemplate {who} category={self.category!r}>"

    def preview(self, path: Optional[str] = None) -> str:
        """Generate an HTML preview page and return its path."""
        from .page import Page  # local import to avoid a cycle

        page = Page(repr(self), body_attrs={
            "style": "min-height:100vh;display:grid;place-items:center;background:#f4f4f5;margin:0"
        })
        page.add(self)
        path = path or os.path.join(_cache_dir(), "preview.html")
        return page.save(path)


def builtin_templates() -> List[str]:
    """Names of the built-in components usable with ``UITemplate.builtin(name)``."""
    return list(_BUILTINS)


# ---------------------------------------------------------------------------
# Built-in components (original Claide designs, MIT license)
# ---------------------------------------------------------------------------
_BUILTINS: Dict[str, Dict[str, str]] = {
    "gradient": {
        "label": "Button",
        "html": '<button class="cl-gradient">Button</button>',
        "css": """.cl-gradient {
  padding: 0.8em 1.8em; border: 0; border-radius: 999px; cursor: pointer;
  font: 600 1rem/1 system-ui, sans-serif; color: #fff;
  background: linear-gradient(120deg, #6366f1, #ec4899, #f59e0b);
  background-size: 200% 100%; transition: background-position .5s, transform .15s;
}
.cl-gradient:hover { background-position: 100% 0; }
.cl-gradient:active { transform: scale(.96); }""",
    },
    "glow": {
        "label": "Button",
        "html": '<button class="cl-glow">Button</button>',
        "css": """.cl-glow {
  padding: 0.8em 1.8em; border: 2px solid #22d3ee; border-radius: 10px; cursor: pointer;
  font: 600 1rem/1 system-ui, sans-serif; color: #22d3ee; background: #0f172a;
  transition: box-shadow .3s, color .3s, background .3s;
}
.cl-glow:hover { color: #0f172a; background: #22d3ee; box-shadow: 0 0 8px #22d3ee, 0 0 32px #22d3ee; }""",
    },
    "slide": {
        "label": "Button",
        "html": '<button class="cl-slide"><span>Button</span></button>',
        "css": """.cl-slide {
  position: relative; overflow: hidden; padding: 0.8em 1.8em; cursor: pointer;
  border: 2px solid #111827; border-radius: 8px; background: transparent;
  font: 600 1rem/1 system-ui, sans-serif; color: #111827; transition: color .3s;
}
.cl-slide::before {
  content: ""; position: absolute; inset: 0; background: #111827;
  transform: translateX(-101%); transition: transform .3s ease;
}
.cl-slide span { position: relative; }
.cl-slide:hover { color: #fff; }
.cl-slide:hover::before { transform: translateX(0); }""",
    },
    "pushable": {
        "label": "Button",
        "html": '<button class="cl-push"><span class="cl-push-front">Button</span></button>',
        "css": """.cl-push { border: 0; padding: 0; border-radius: 12px; background: #b91c1c; cursor: pointer; }
.cl-push-front {
  display: block; padding: 0.75em 1.8em; border-radius: 12px; background: #ef4444;
  font: 700 1rem/1 system-ui, sans-serif; color: #fff;
  transform: translateY(-6px); transition: transform .12s;
}
.cl-push:hover .cl-push-front { transform: translateY(-8px); }
.cl-push:active .cl-push-front { transform: translateY(-2px); }""",
    },
    "spinner": {
        "label": "",
        "html": '<div class="cl-spinner" role="status" aria-label="Loading"></div>',
        "css": """.cl-spinner {
  width: 42px; height: 42px; border-radius: 50%;
  border: 4px solid #e5e7eb; border-top-color: #6366f1; animation: cl-spin .8s linear infinite;
}
@keyframes cl-spin { to { transform: rotate(360deg); } }""",
    },
    "toggle": {
        "label": "",
        "html": '<label class="cl-toggle"><input type="checkbox"><span></span></label>',
        "css": """.cl-toggle { position: relative; display: inline-block; width: 52px; height: 28px; }
.cl-toggle input { opacity: 0; width: 0; height: 0; }
.cl-toggle span {
  position: absolute; inset: 0; cursor: pointer; border-radius: 999px; background: #d1d5db; transition: background .25s;
}
.cl-toggle span::before {
  content: ""; position: absolute; left: 3px; top: 3px; width: 22px; height: 22px;
  border-radius: 50%; background: #fff; transition: transform .25s; box-shadow: 0 1px 3px #0003;
}
.cl-toggle input:checked + span { background: #22c55e; }
.cl-toggle input:checked + span::before { transform: translateX(24px); }""",
    },
    "card": {
        "label": "Title",
        "html": '<div class="cl-card"><h3>Title</h3><p>Card description.</p></div>',
        "css": """.cl-card {
  max-width: 320px; padding: 1.5rem; border-radius: 16px; background: #fff;
  font-family: system-ui, sans-serif; box-shadow: 0 10px 30px -12px #0004;
  transition: transform .25s, box-shadow .25s;
}
.cl-card:hover { transform: translateY(-4px); box-shadow: 0 18px 40px -12px #0005; }
.cl-card h3 { margin: 0 0 .5rem; }
.cl-card p { margin: 0; color: #4b5563; }""",
    },
}
