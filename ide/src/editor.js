// CodeMirror 6 editor with a monochrome theme (weight and style instead of colors).
import { EditorView, basicSetup } from "codemirror";
import { EditorState, Compartment } from "@codemirror/state";
import { keymap } from "@codemirror/view";
import { indentUnit, HighlightStyle, LanguageSupport, syntaxHighlighting } from "@codemirror/language";
import { styleTags } from "@lezer/highlight";
import { indentWithTab } from "@codemirror/commands";
import { tags as t } from "@lezer/highlight";
import { python, pythonLanguage } from "@codemirror/lang-python";
import { autocompletion, snippetCompletion as snip } from "@codemirror/autocomplete";
import { syntaxTree } from "@codemirror/language";
import { css } from "@codemirror/lang-css";
import { javascript } from "@codemirror/lang-javascript";
import { html } from "@codemirror/lang-html";

// Colors come from CSS variables, so the light and dark themes each get their own palette.
const colors = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.definitionKeyword, t.moduleKeyword, t.operatorKeyword], color: "var(--tok-keyword)" },
  { tag: [t.function(t.definition(t.variableName)), t.function(t.variableName), t.function(t.propertyName)], color: "var(--tok-function)" },
  { tag: [t.definition(t.className), t.className, t.typeName], color: "var(--tok-class)" },
  { tag: [t.self, t.standard(t.variableName), t.special(t.variableName)], color: "var(--tok-builtin)" },
  { tag: [t.string, t.special(t.string), t.regexp, t.docString], color: "var(--tok-string)" },
  { tag: [t.comment, t.lineComment, t.blockComment], color: "var(--tok-comment)", fontStyle: "italic" },
  { tag: [t.number, t.integer, t.float, t.bool, t.null, t.atom, t.unit, t.color], color: "var(--tok-number)" },
  { tag: [t.meta, t.annotation, t.processingInstruction], color: "var(--tok-decorator)" },
  { tag: [t.propertyName, t.attributeName], color: "var(--tok-property)" },
  { tag: [t.tagName, t.heading], color: "var(--tok-tag)" },
  { tag: [t.escape, t.special(t.brace)], color: "var(--tok-number)" },
  { tag: t.invalid, textDecoration: "underline wavy" },
]);

const theme = EditorView.theme({
  "&": { height: "100%", fontSize: "13px", backgroundColor: "var(--bg)", color: "var(--text)" },
  "&.cm-focused": { outline: "none" },
  ".cm-scroller": { fontFamily: 'ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, "DejaVu Sans Mono", monospace', lineHeight: "1.6" },
  ".cm-content": { caretColor: "var(--text)", padding: "8px 0" },
  ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--text)", borderLeftWidth: "2px" },
  ".cm-gutters": { backgroundColor: "var(--bg)", color: "var(--faint)", border: "none", paddingRight: "4px" },
  ".cm-activeLine": { backgroundColor: "var(--panel)" },
  ".cm-activeLineGutter": { backgroundColor: "var(--panel)", color: "var(--text)" },
  "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection": { backgroundColor: "var(--select) !important" },
  ".cm-matchingBracket, .cm-nonmatchingBracket": { backgroundColor: "var(--select)", outline: "1px solid var(--line-strong)" },
  ".cm-selectionMatch": { backgroundColor: "var(--panel-2)" },
  ".cm-searchMatch": { backgroundColor: "var(--panel-2)", outline: "1px solid var(--line-strong)" },
  ".cm-tooltip, .cm-panels": { backgroundColor: "var(--panel)", color: "var(--text)", border: "1px solid var(--line-strong)" },
  ".cm-tooltip-autocomplete ul li[aria-selected]": { backgroundColor: "var(--select)", color: "var(--text)" },
  ".cm-tooltip-autocomplete ul li": { padding: "2px 8px 2px 4px !important" },
  ".cm-tooltip-autocomplete > ul": { fontFamily: 'ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace', maxHeight: "16em" },
  ".cm-completionLabel": { color: "var(--text)" },
  ".cm-completionMatchedText": { textDecoration: "none", fontWeight: "700" },
  ".cm-completionDetail": { color: "var(--faint)", fontStyle: "normal", marginLeft: "10px" },
  ".cm-tooltip.cm-completionInfo": { padding: "8px 10px", maxWidth: "360px", lineHeight: "1.45", fontFamily: "system-ui, sans-serif" },
  ".cm-completionIcon": { opacity: "1", width: "1.2em", color: "var(--muted)" },
  ".cm-completionIcon-snippet:after": { content: "'{}'", fontSize: "11px", fontWeight: "700" },
  ".cm-snippetField": { backgroundColor: "var(--panel-2)" },
  ".cm-snippetFieldPosition": { borderLeft: "2px solid var(--text)" },
  ".cm-foldPlaceholder": { backgroundColor: "var(--panel-2)", border: "none", color: "var(--muted)" },
  ".cm-panel input, .cm-panel button": { color: "var(--text)" },
});

// ---- Claide completions -----------------------------------------------------
// Names, signatures and docs come from completions.json, generated at build time
// by inspecting the Claide module. Snippets add ready-made pieces of code.
let claide = { globals: [], request: [], ui: [] };
fetch("completions.json").then((r) => r.json()).then((data) => { claide = data; }).catch(() => {});

const SNIPPETS = [
  snip('from claide import *\n\n\n@route("/")\ndef home():\n    return h1("${Hello!}")\n\n\nrun()\n',
    { label: "claide", detail: "new site", info: "A complete Claide site: one page and run().", type: "snippet", boost: 2 }),
  snip('@route("/${page}")\ndef ${page}():\n    return h1("${Title}"), p("${Text}")',
    { label: "route", detail: "page", info: "A new page: @route + function returning elements.", type: "snippet", boost: 3 }),
  snip('@get("/api/${name}")\ndef ${name}():\n    return {"${key}": ${value}}',
    { label: "get", detail: "JSON API", info: "A GET route that answers JSON.", type: "snippet", boost: 2 }),
  snip('@post("/api/${name}")\ndef ${name}(${field}: str):\n    return {"ok": True, "${field}": ${field}}',
    { label: "post", detail: "API that receives data", info: "A POST route: form or JSON fields arrive as parameters.", type: "snippet", boost: 2 }),
  snip('form(\n    label("${Name}", input_(name="${name}")),\n    button("${Send}"),\n    method="post",\n)',
    { label: "form", detail: "form", info: "A form sent with POST. Field names become parameters of the route.", type: "snippet", boost: 2 }),
  snip('if request.method == "POST":\n    ${}',
    { label: "ifpost", detail: "form sent?", info: "Run code only when the form was submitted.", type: "snippet" }),
  snip('@layout\ndef base(page):\n    page.body.children.insert(0, nav(a("Home", href="/"), " ", a("${About}", href="/${about}")))',
    { label: "layout", detail: "navbar on every page", info: "Function applied to every page.", type: "snippet", boost: 1 }),
  snip('@error(404)\ndef not_found():\n    return h1("Page not found"), p(a("Back home", href="/"))',
    { label: "error", detail: "404 page", info: "Custom page for a missing address.", type: "snippet" }),
  snip('md("""\n    # ${Title}\n\n    ${Some **bold** text.}\n""")',
    { label: "md", detail: "Markdown", info: "Write content in Markdown.", type: "snippet", boost: 1 }),
  snip('ui("${author/name}")',
    { label: "ui", detail: "Uiverse component", info: "Component from uiverse.io: copy the author/name from its URL.", type: "snippet", boost: 1 }),
  snip('ui.builtin("${glow}", "${Send}")',
    { label: "ui.builtin", detail: "built-in component", info: "gradient, glow, slide, pushable, spinner, toggle, card.", type: "snippet" }),
  snip('request.session["${key}"] = ${value}',
    { label: "session", detail: "remember a value", info: "Keep a value between pages for this visitor.", type: "snippet" }),
  snip('return redirect("${/}")',
    { label: "redirect", detail: "go to another page", info: "Send the visitor to another address.", type: "snippet" }),
  snip('a("${text}", href="${/}")', { label: "a", detail: "link", info: "A link: a(\"text\", href=\"/page\").", type: "snippet" }),
  snip('img(src="/static/${image.png}", alt="${}")', { label: "img", detail: "image", info: "An image from the static folder.", type: "snippet" }),
];

const KIND = { function: "function", class: "class", tag: "type", variable: "variable", namespace: "namespace",
  constant: "constant", method: "method", property: "property" };
const toOption = (item) => ({ label: item.label, type: KIND[item.type] || "variable", detail: item.detail || "", info: item.info || undefined });

function claideCompletions(context) {
  const node = syntaxTree(context.state).resolveInner(context.pos, -1);
  if (/String|Comment/.test(node.name)) return null;
  const member = context.matchBefore(/\b(request|ui|UITemplate|\))\.\w*$/);
  if (member) {
    const owner = member.text.split(".")[0];
    const line = context.state.doc.lineAt(context.pos).text;
    const list = owner === "request" ? claide.request
      : owner === "ui" || owner === "UITemplate" || (owner === ")" && /\bui[.(]/.test(line)) ? claide.ui : null;
    if (!list) return null;
    return { from: member.from + owner.length + 1, options: list.map(toOption), validFor: /^\w*$/ };
  }
  const word = context.matchBefore(/@?\w+$/);
  if (!word && !context.explicit) return null;
  const from = word ? word.from + (word.text.startsWith("@") ? 1 : 0) : context.pos;
  return {
    from,
    options: [...SNIPPETS, ...claide.globals.map(toOption)],
    validFor: /^\w*$/,
  };
}

const claideSupport = pythonLanguage.data.of({ autocomplete: claideCompletions });

// Python with the whole decorator (@route, @get...) colored, not only the "@".
const pythonColored = (() => {
  const base = python();
  const lang = pythonLanguage.configure({
    props: [styleTags({ "Decorator/VariableName Decorator/PropertyName": t.meta })],
  });
  return new LanguageSupport(lang, base.support);
})();

function languageFor(path) {
  if (path.endsWith(".py")) return [pythonColored, claideSupport, indentUnit.of("    ")];
  if (path.endsWith(".css")) return [css(), indentUnit.of("  ")];
  if (/\.(m?js|json)$/.test(path)) return [javascript(), indentUnit.of("  ")];
  if (/\.(html?|svg)$/.test(path)) return [html(), indentUnit.of("  ")];
  return [indentUnit.of("  ")];
}

export function createEditor(parent, { onChange, onRun }) {
  const lang = new Compartment();
  const view = new EditorView({
    parent,
    state: EditorState.create({ doc: "", extensions: [] }),
  });
  const extensions = () => [
    basicSetup,
    theme,
    syntaxHighlighting(colors),
    autocompletion({ activateOnTyping: true, icons: true, maxRenderedOptions: 40 }),
    keymap.of([
      indentWithTab,
      { key: "Mod-Enter", run: () => { onRun(); return true; } },
      { key: "Mod-s", run: () => { onRun(); return true; }, preventDefault: true },
    ]),
    EditorView.updateListener.of((u) => { if (u.docChanged) onChange(u.state.doc.toString()); }),
  ];
  return {
    view,
    open(path, text) {
      view.setState(EditorState.create({ doc: text, extensions: [...extensions(), lang.of(languageFor(path))] }));
    },
    focus() { view.focus(); },
  };
}
