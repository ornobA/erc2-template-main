# -*- coding: utf-8 -*-
"""
Find the tooling that ships inside the installed ERC2 library package.

The ERC2 library carries its own host-side tooling -- the upload hooks and
ERC2 Link -- under ``bin/host/``. This project only keeps small stubs that
locate that directory and hand over, so the tooling updates with the library
instead of through a separate channel.

Nothing here should ever need changing: it knows only how to find a directory.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def find_host_dir(libdeps_root: str | Path, env_name: str = "") -> Path | None:
    """Locate ``bin/host/`` inside the installed ERC2 library.

    Handles the registry install (``<libdeps>/<env>/ERC2/``) and a local
    symlink dependency, which PlatformIO records as a ``<name>.pio-link`` JSON
    pointer rather than a real directory.
    """
    root = Path(libdeps_root)
    candidates = [root / env_name, root] if env_name else [root]

    for start in candidates:
        if not start.is_dir():
            continue
        for host in start.glob("*/bin/host"):
            if host.is_dir():
                return host

        # Symlinked (developer) dependency: resolve the .pio-link pointer.
        for link in start.glob("*.pio-link"):
            try:
                info = json.loads(link.read_text(encoding="utf-8"))
                uri = info.get("spec", {}).get("uri", "")
                if not uri.startswith("symlink://"):
                    continue
                target = (Path(info.get("cwd", ".")) / uri[len("symlink://"):]).resolve()
                host = target / "bin" / "host"
                if host.is_dir():
                    return host
            except Exception:
                continue
    return None


def load_module(path: Path, name: str):
    """Import a Python file from the installed package by path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def warn(msg: str) -> None:
    print(f"\033[93m[ERC2]\033[0m {msg}", flush=True)
