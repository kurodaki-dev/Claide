"""Classless theme: makes plain HTML look clean without writing any CSS.

Enabled with ``App(theme=True)`` (and by default with ``@route`` / ``run()``).
Only bare elements are styled, so your own stylesheets can override anything.
"""

THEME_CSS = """:root {
  --c-bg: #fbfaf7; --c-text: #1f1e1b; --c-muted: #6b6860; --c-line: #e3e0d8;
  --c-accent: #1d4ed8; --c-code: #f2f0ea;
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root { --c-bg: #161614; --c-text: #ebe8df; --c-muted: #a19d93; --c-line: #34322d;
          --c-accent: #8ab4ff; --c-code: #23221f; }
}
html { background: var(--c-bg); }
body {
  box-sizing: border-box; max-width: calc(46rem + 40px); margin: 0 auto; padding: 32px 20px 56px;
  background: var(--c-bg); color: var(--c-text);
  font: 17px/1.65 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
/* Full-width blocks from claide.components break out of the centered column. */
body > :where(.cl-nav, .cl-hero, .cl-section, .cl-footer) { margin-inline: calc(50% - 50vw); }
body > :where(.cl-nav:first-child) { margin-top: -32px; }
h1, h2, h3, h4 { line-height: 1.2; letter-spacing: -.01em; margin: 1.6em 0 .5em; }
:where(h1, h2, h3, h4):first-child, nav + :where(h1, h2, h3) { margin-top: .6em; }
h1 { font-size: 2.3rem; } h2 { font-size: 1.6rem; } h3 { font-size: 1.25rem; }
p, ul, ol, pre, table, form, blockquote, figure { margin: 0 0 1.1em; }
a { color: var(--c-accent); text-underline-offset: .15em; }
img, video { max-width: 100%; height: auto; }
hr { border: 0; border-top: 1px solid var(--c-line); margin: 2em 0; }
small { color: var(--c-muted); }
code, pre, kbd { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: .9em; }
:not(pre) > code { background: var(--c-code); padding: .1em .35em; border-radius: 4px; }
pre { background: var(--c-code); padding: 14px 16px; border-radius: 6px; overflow-x: auto; line-height: 1.5; }
blockquote { margin-inline: 0; padding-left: 1em; border-left: 3px solid var(--c-line); color: var(--c-muted); }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--c-line); }
th { font-weight: 600; }
form:where(:not(.cl-form)) { display: grid; gap: 14px; }
form:where(:not(.cl-form)) > :where(button, input[type=submit]) { justify-self: start; }
label:has(> :where(input:not([type=checkbox]):not([type=radio]), select, textarea)) { display: grid; gap: 4px; }
label { font-weight: 500; }
input:where(:not([type=checkbox]):not([type=radio]):not([type=submit]):not([type=button])), select, textarea {
  box-sizing: border-box; font: inherit; width: 100%; padding: 9px 11px; color: inherit; background: var(--c-bg);
  border: 1px solid var(--c-line); border-radius: 6px;
}
input:focus-visible, select:focus-visible, textarea:focus-visible { outline: 2px solid var(--c-accent); outline-offset: 1px; }
:where(button, input[type=submit], input[type=button]) {
  font: inherit; font-weight: 600; padding: 9px 18px; border: 0; border-radius: 6px; cursor: pointer;
  color: #fff; background: var(--c-accent);
}
:where(button, input[type=submit], input[type=button]):hover { filter: brightness(1.1); }
nav ul { display: flex; flex-wrap: wrap; gap: 6px 20px; list-style: none; padding: 0; margin: 0; }
nav { padding-bottom: 14px; border-bottom: 1px solid var(--c-line); }
nav a { text-decoration: none; font-weight: 500; }
nav a:hover { text-decoration: underline; }
"""
