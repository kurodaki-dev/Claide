// Small line icons (monochrome, drawn with currentColor).
const paths = {
  play: '<path d="M5 3.5v9l7.5-4.5z"/>',
  plus: '<path d="M8 3v10M3 8h10"/>',
  file: '<path d="M4 2h5l3 3v9H4z"/><path d="M9 2v3h3"/>',
  folder: '<path d="M2 4.5h4l1.5 1.5H14v7H2z"/>',
  chevron: '<path d="M4.5 6l3.5 3.5L11.5 6"/>',
  trash: '<path d="M3 4.5h10M6.5 4.5V3h3v1.5M4.5 4.5l.7 9h5.6l.7-9"/>',
  edit: '<path d="M3 13l.6-2.6L10.5 3.5l2 2-6.9 6.9z"/>',
  download: '<path d="M8 2.5v8M4.5 7L8 10.5 11.5 7M3 13.5h10"/>',
  upload: '<path d="M8 10.5v-8M4.5 6L8 2.5 11.5 6M3 13.5h10"/>',
  reload: '<path d="M12.5 8a4.5 4.5 0 1 1-1.3-3.2"/><path d="M12.5 2.5v2.8H9.7"/>',
  sun: '<circle cx="8" cy="8" r="2.8"/><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1 1M11.6 11.6l1 1M3.4 12.6l1-1M11.6 4.4l1-1"/>',
  moon: '<path d="M13 9.5A5.5 5.5 0 0 1 6.5 3a5.5 5.5 0 1 0 6.5 6.5z"/>',
  auto: '<circle cx="8" cy="8" r="5.5"/><path d="M8 2.5v11" /><path d="M8 2.5a5.5 5.5 0 0 1 0 11z" fill="currentColor"/>',
  code: '<path d="M6 4.5L2.5 8 6 11.5M10 4.5L13.5 8 10 11.5"/>',
  eye: '<path d="M1.5 8S4 3.5 8 3.5 14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8z"/><circle cx="8" cy="8" r="2"/>',
  terminal: '<path d="M2.5 3.5h11v9h-11z"/><path d="M5 6.5l2 1.5-2 1.5M8.5 10h2.5"/>',
  external: '<path d="M9 2.5h4.5V7M13.5 2.5L7.5 8.5M11.5 9.5v4h-9v-9h4"/>',
  open: '<path d="M2 4.5h4l1.5 1.5H14v2"/><path d="M2 4.5v8.5h10.5L14 8H4z"/>',
  clear: '<path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/>',
};
export const icon = (name) => `<svg class="i" viewBox="0 0 16 16" aria-hidden="true">${paths[name] || ""}</svg>`;
export const logo = `<svg viewBox="0 0 64 64" aria-hidden="true"><g fill="currentColor"><path d="M3 14C11 3 21 2 32 9S53 17 61 6C55 21.4 44 24.25 32 17.5S11 10.275 3 14Z"/><path d="M3 31C11 20 21 19 32 26S53 34 61 23C55 38.4 44 41.25 32 34.5S11 27.275 3 31Z"/><path d="M3 48C11 37 21 36 32 43S53 51 61 40C55 55.4 44 58.25 32 51.5S11 44.275 3 48Z"/></g></svg>`;
