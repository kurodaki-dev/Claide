# Claide IDE

Claide IDE is an application to write, run and preview Claide websites. Python runs **inside the app** (compiled to WebAssembly with Pyodide), so there is nothing else to install, not even Python, and it works offline.

## Download

Get the latest version from the [releases page](https://github.com/kurodaki-dev/Claide/releases/latest):

| Platform | File | How to install |
|---|---|---|
| Windows | `Claide-IDE-Setup-*.exe` | run the installer |
| Windows | `Claide-IDE-*-portable.exe` | no installation: double-click to start |
| Linux | `*.AppImage` | `chmod +x Claide-IDE-*.AppImage`, then run it |
| Linux | `*.deb` | `sudo apt install ./Claide-IDE-*.deb` (Debian, Ubuntu) |
| Android | `Claide-IDE-*.apk` | open the file on your phone and allow installing apps from this source |

> The Windows files are not signed, so Windows SmartScreen may warn you the first time: choose **More info**, then **Run anyway**.

## What you get

- **Projects**: create one from the starter template, start from an empty `app.py`, or import a `.zip`. On Windows and Linux, **Open folder** edits a project folder on your disk directly, so you can also run it with `python app.py`.
- **Editor**: Python, CSS, JavaScript and HTML in color (a palette for the light theme and one for the dark theme), with indentation, search (`Ctrl+F`), multiple cursors and code folding.
- **Suggestions while you type**: every Claide name with its signature and description (`route`, `request`, `md`, `ui`, all the HTML tags...), the members of `request.` and `ui.`, and ready-made pieces of code: type `route`, `form`, `get`, `post`, `layout`, `md` or `claide` and press `Enter`, then `Tab` to go from one field to fill to the next. The list is generated from Claide itself, so it always matches the version inside the app.
- **Live preview**: the site reloads a moment after you stop typing (or press `Ctrl+Enter`). Links, forms, sessions and `fetch()` calls work inside the preview. Pick a page from the **Pages** list or type an address.
- **Console**: `print()` output and errors, with the file and line that caused them.
- **Several files**: add files under `routes/` and their routes appear immediately.
- **Uiverse components**: `ui("author/name")` downloads the component once into `templates/`, where you can edit it.
- **Export**: download the project as a `.zip`, ready to run with `python app.py`.
- **Fast start**: Python is prepared when the app is built and restored in a fraction of a second when it opens, even the very first time.
- **Light and dark themes** (follows your system by default), and a layout for phones with **Files**, **Code** and **Preview** tabs. On Android the app runs full screen: swipe from the top or bottom edge to see the system bars for a moment.

## Shortcuts

| Keys | Action |
|---|---|
| `Ctrl+Enter` / `Cmd+Enter` | run |
| `Ctrl+S` | save and run |
| `Ctrl+F` | search in the file |
| `Tab` / `Shift+Tab` | indent / unindent |
| `Ctrl+/` | comment the line |
| `Ctrl+Space` | show the suggestions |
| `Enter` / `Tab` | accept a suggestion / go to the next field of a snippet |

## Where are my projects?

Projects created in the app are stored on the device, in the app's own storage. Use **Export** to make a copy, or, on desktop, **Open folder** to work directly with files on disk.

## Building the IDE yourself

The IDE lives in the [`ide/`](https://github.com/kurodaki-dev/Claide/tree/main/ide) folder of the repository:

```bash
cd ide
npm install
npm start              # run the desktop app
npm run dist:win       # Windows installer and portable .exe
npm run dist:linux     # AppImage and .deb
npm run android:sync   # then build the APK with Android Studio or ./gradlew
```

Every push to `main` builds all three platforms with GitHub Actions and publishes them on the releases page.
