# Command line

Installing Claide adds a `claide` command (also available as `python -m claide`).

| Command | Description |
|---|---|
| `claide new NAME` | create a new project in the `NAME` folder |
| `claide run [app:app]` | start the server (`--host`, `--port`, `--prod`) |
| `claide build [app:app]` | export the site as static HTML (`--out dist`) |
| `claide ui REF` | download a Uiverse component (`--preview`, `--save FILE`, `--category`) |
| `claide --version` | show the installed version |

## Examples

```bash
claide new blog
claide run app:app --port 5000
claide build app:app --out public
claide ui https://uiverse.io/0x-Sarthak/hungry-penguin-30 --save button.html
```

The `app:app` target means "the `app` object in the `app.py` module". If your file is `server.py` and the object is `site`, use `claide run server:site`.
