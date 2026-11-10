"""Multi-threaded development server with auto-reload."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from socketserver import ThreadingMixIn
from typing import Callable, Dict, Iterator
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

_CHILD_ENV = "CLAIDE_RELOADER_CHILD"
_WATCH_EXT = (".py", ".css", ".js", ".html", ".json", ".svg")


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = True


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        sys.stderr.write(f"  {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}\n")


def _iter_files(root: str) -> Iterator[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith((".", "__pycache__", "node_modules", "dist", "venv"))]
        for f in filenames:
            if f.endswith(_WATCH_EXT):
                yield os.path.join(dirpath, f)


def _snapshot(root: str) -> Dict[str, float]:
    snap = {}
    for path in _iter_files(root):
        try:
            snap[path] = os.stat(path).st_mtime
        except OSError:
            pass
    return snap


def _run_with_reloader(root: str) -> None:
    """Parent process: restart the script whenever a file changes."""
    while True:
        env = dict(os.environ, **{_CHILD_ENV: "1"})
        proc = subprocess.Popen([sys.executable, *sys.argv], env=env)
        before = _snapshot(root)
        try:
            while proc.poll() is None:
                time.sleep(0.7)
                if _snapshot(root) != before:
                    print("  ↻ Change detected, restarting...", file=sys.stderr)
                    proc.terminate()
                    proc.wait()
                    break
            else:
                sys.exit(proc.returncode)
        except KeyboardInterrupt:
            proc.terminate()
            proc.wait()
            return


def run_server(app: Callable, host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    root = getattr(app, "root", os.getcwd())
    main = sys.modules.get("__main__")
    can_reload = reload and getattr(main, "__file__", None) is not None
    if can_reload and os.environ.get(_CHILD_ENV) != "1":
        print(f"\n  Claide running on http://{host}:{port}  (Ctrl+C to quit, auto-reload on)\n",
              file=sys.stderr)
        _run_with_reloader(root)
        return
    if not can_reload:
        print(f"\n  Claide running on http://{host}:{port}  (Ctrl+C to quit)\n", file=sys.stderr)
    with make_server(host, port, app, server_class=_ThreadingWSGIServer, handler_class=_QuietHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
