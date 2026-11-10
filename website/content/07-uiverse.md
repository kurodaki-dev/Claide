# Uiverse components

[Uiverse.io](https://uiverse.io) (and [cssbuttons.io](https://cssbuttons.io), which redirects to its buttons) hosts thousands of open-source UI elements: buttons, cards, loaders, inputs, toggles... `UITemplate` lets you use any of them in one line.

## Using a component

Open an element on uiverse.io and copy its URL:

```python
from claide import UITemplate          # or: from claide import uitemplate

button = UITemplate("https://uiverse.io/0x-Sarthak/hungry-penguin-30")
# same thing:
button = UITemplate("0x-Sarthak/hungry-penguin-30")

page.add(button)
```

The component's CSS is **injected automatically** into the `<head>`, only once, even if you use the component many times.

> Components are downloaded from [uiverse-io/galaxy](https://github.com/uiverse-io/galaxy), the official archive of Uiverse (MIT license), and **saved in a `templates` folder** next to your code. Only the first use needs Internet access.

## Customizing

Every method returns a **new** template, so you can reuse the original:

```python
cta = (
    button
    .text("Contact Us", "Write to me")      # replace visible text (escaped)
    .attrs(id="send", onclick="send()")    # attributes on the root element
    .add_css(".cta { background: crimson }")
    .link("/contact")                      # wrap it in <a href>
)
```

| Method | What it does |
|---|---|
| `.text(old, new)` | replace a visible text |
| `.text(new)` | replace the first text found |
| `.attrs(**attrs)` | add attributes (`class_` is appended) |
| `.link(href)` | wrap in a link |
| `.add_css(css)` / `.add_js(js)` | add CSS / JS |
| `.replace(old, new, css=False)` | raw replacement in HTML or CSS |
| `.scoped()` | isolate the component's CSS from the rest of the page |
| `.prefix("x-")` | rename CSS classes with your prefix |
| `.preview()` | write a preview HTML file and return its path |

## Avoiding CSS conflicts

Some Uiverse components style plain tags (`button { ... }`) or ids (`#timer`), and two components can use the same class name (often `.button`). Without isolation, that CSS applies to your **whole page**. Use `.scoped()`:

```python
a = UITemplate("author1/button-1").scoped()
b = UITemplate("author2/button-2").scoped()
```

The component is rendered inside an invisible wrapper (`display: contents`) with a unique class, every selector is prefixed with it, and `@keyframes` names are renamed:

```css
/* before */                        /* after .scoped() */
button { color: red }               .u1a2b3c button { color: red }
@keyframes spin { ... }             @keyframes u1a2b3c-spin { ... }
```

`.text()`, `.attrs()` and `.add_css()` keep working after `.scoped()`. Use `.prefix("x-")` if you prefer to rename the classes themselves.

## Tailwind components

Some Uiverse elements are written with Tailwind CSS classes instead of a `<style>` block. Claide detects them and loads the Tailwind CDN automatically. Force it with `UITemplate(..., tailwind=True)`.

## Categories

When you know the category, pass it to skip the search:

```python
UITemplate("author/name", category="loaders")
```

Available: `Buttons`, `Cards`, `Checkboxes`, `Forms`, `Inputs`, `loaders`, `Notifications`, `Patterns`, `Radio-buttons`, `Toggle-switches`, `Tooltips`.

## The `templates` folder

The first time a component is used, Claide saves it as an HTML file in a `templates` folder next to the Python file that uses it:

```text
mysite/
├── app.py
├── static/
└── templates/
    ├── 0x-Sarthak_hungry-penguin-30.html
    └── adamgiebl_big-moose-23.html
```

From then on, the component is read from that file:

- your site **works offline** and builds without downloading anything;
- the components are **part of your project**: commit the folder with the rest of your code;
- you can **edit the file** (colors, text, sizes): your version is the one used. Delete the file to get the original back.

Each file starts with a comment giving the author, the Uiverse link and the license, followed by the component's HTML and its `<style>`.

| Option | Effect |
|---|---|
| `UITemplate(ref, save=False)` | don't write anything, keep the component in memory |
| `UITemplate(ref, folder="ui")` | use another folder |
| `CLAIDE_TEMPLATES_DIR=/path` | environment variable: same folder for the whole project |

## Your own components

Put your own components in the same folder and load them by name:

```python
UITemplate.local("my-button")          # templates/my-button.html
```

A component file is plain HTML, followed by an optional `<style>` and `<script>`. You can also save any component there:

```python
ui.builtin("glow", "Send").save("send-button")   # -> templates/send-button.html
```

Other ways to create a component:

```python
UITemplate(html="<button class='btn'>OK</button>", css=".btn { color: red }")
UITemplate.from_file("components/button.html")   # HTML + <style> + <script>
UITemplate.from_source(pasted_code)
```

## Built-in components

These come with Claide and work offline:

```python
UITemplate.builtin("glow", "Send")
```

Available: `gradient`, `glow`, `slide`, `pushable`, `spinner`, `toggle`, `card`. See them live on the [home page](/#showcase).

## Command line

```bash
claide ui 0x-Sarthak/hungry-penguin-30             # download into ./templates
claide ui 0x-Sarthak/hungry-penguin-30 --preview   # ... and open a preview file
```

> Uiverse elements are MIT licensed. Claide adds a credit comment with the author's name in the CSS; crediting authors on your site is appreciated.
