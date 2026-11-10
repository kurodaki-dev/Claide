"""Tiny Markdown -> Claide converter used by the documentation site.

Supports: #/##/### headings, paragraphs, fenced code blocks, inline code,
**bold**, *italic*, [links](url), - / 1. lists, > callouts and pipe tables.
"""

from __future__ import annotations

import re
from typing import Callable, List, Tuple

from claide import escape, raw

_INLINE_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>|`", "", text).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def inline(text: str, url: Callable[[str], str]) -> str:
    codes: List[str] = []

    def keep_code(m: "re.Match[str]") -> str:
        codes.append(f"<code>{escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = _INLINE_CODE.sub(keep_code, text)
    text = escape(text)
    text = _LINK.sub(lambda m: f'<a href="{escape(url(m.group(2)))}">{m.group(1)}</a>', text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    return re.sub("\x00(\\d+)\x00", lambda m: codes[int(m.group(1))], text)


def render(source: str, url: Callable[[str], str] = lambda u: u) -> Tuple[str, str, List[Tuple[str, str]]]:
    """Return (title, html, toc) where toc lists the (id, text) of ## headings."""
    lines = source.strip("\n").splitlines()
    out: List[str] = []
    toc: List[Tuple[str, str]] = []
    title = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "plaintext"
            i += 1
            code: List[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            out.append(f'<pre><code class="language-{escape(lang)}">{escape(chr(10).join(code))}</code></pre>')
            continue
        m = re.match(r"(#{1,3})\s+(.*)", stripped)
        if m:
            level, text = len(m.group(1)), m.group(2)
            if level == 1:
                title = re.sub(r"`", "", text)
                out.append(f"<h1>{inline(text, url)}</h1>")
            else:
                hid = slugify(text)
                if level == 2:
                    toc.append((hid, re.sub(r"`", "", text)))
                out.append(f'<h{level} id="{hid}"><a class="anchor" href="#{hid}">#</a>{inline(text, url)}</h{level}>')
            i += 1
            continue
        if stripped.startswith(">"):
            quote: List[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f'<div class="callout">{inline(" ".join(quote), url)}</div>')
            continue
        if stripped.startswith("|"):
            rows: List[List[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            head = "".join(f"<th>{inline(c, url)}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(c, url)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
            continue
        list_m = re.match(r"(-|\d+\.)\s+", stripped)
        if list_m:
            tag = "ul" if list_m.group(1) == "-" else "ol"
            items: List[str] = []
            while i < len(lines) and re.match(r"\s*(-|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*(-|\d+\.)\s+", "", lines[i]))
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
                    items[-1] += " " + lines[i].strip()
                    i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(it, url)}</li>" for it in items) + f"</{tag}>")
            continue
        para: List[str] = []
        while i < len(lines) and lines[i].strip() and not re.match(r"\s*(#|```|>|\||-\s|\d+\.\s)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para), url)}</p>")
    return title, raw("\n".join(out)), toc
