// CodeMirror 6 editor with a monochrome theme (weight and style instead of colors).
import { EditorView, basicSetup } from "codemirror";
import { EditorState, Compartment } from "@codemirror/state";
import { keymap } from "@codemirror/view";
import { indentUnit, HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { indentWithTab } from "@codemirror/commands";
import { tags as t } from "@lezer/highlight";
import { python } from "@codemirror/lang-python";
import { css } from "@codemirror/lang-css";
import { javascript } from "@codemirror/lang-javascript";
import { html } from "@codemirror/lang-html";

const mono = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.definitionKeyword, t.moduleKeyword, t.operatorKeyword], fontWeight: "650" },
  { tag: [t.function(t.definition(t.variableName)), t.definition(t.className)], fontWeight: "650" },
  { tag: [t.string, t.special(t.string), t.regexp], color: "var(--muted)" },
  { tag: [t.comment, t.lineComment, t.blockComment], color: "var(--faint)", fontStyle: "italic" },
  { tag: [t.number, t.bool, t.null, t.atom], color: "var(--muted)", fontWeight: "500" },
  { tag: [t.meta, t.annotation], color: "var(--muted)", fontStyle: "italic" },
  { tag: [t.tagName, t.propertyName], fontWeight: "550" },
  { tag: [t.attributeName], color: "var(--muted)" },
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
  ".cm-foldPlaceholder": { backgroundColor: "var(--panel-2)", border: "none", color: "var(--muted)" },
  ".cm-panel input, .cm-panel button": { color: "var(--text)" },
});

function languageFor(path) {
  if (path.endsWith(".py")) return [python(), indentUnit.of("    ")];
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
    syntaxHighlighting(mono),
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
