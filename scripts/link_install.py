# -*- coding: utf-8 -*-
"""
PlatformIO build hook — installs ERC2 Link, the VS Code extension.

This is a stub. The hook itself ships inside the ERC2 library package
(``bin/host/hooks/link_install.py``), next to the copy of the extension it
installs, so the panel always matches the library this project builds with;
this file only finds it and hands over.

The work happens as a pre-build action, by which point PlatformIO has
installed the library -- so the lookup always succeeds even on a first build
of a fresh checkout, where libdeps do not exist yet at config time.

Environment overrides (for testing and troubleshooting):
    ERC2_LINK=skip     never install the extension
    ERC2_LINK=force    install even when the same version is already there
"""

import sys
from pathlib import Path

Import("env")  # noqa: F821 — injected by PlatformIO

PROJECT_DIR = Path(env.subst("$PROJECT_DIR")).resolve()  # noqa: F821
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from _erc2_package import find_host_dir, load_module, warn  # noqa: E402

_done = False


def _pre_build(target, source, env) -> None:
    global _done
    if _done:  # Once per build, however many targets ask.
        return
    _done = True
    try:
        host = find_host_dir(env.subst("$PROJECT_LIBDEPS_DIR"), env.subst("$PIOENV"))
        if host is None or not (host / "hooks" / "link_install.py").is_file():
            return  # A library from before the extension shipped in it.
        hook = load_module(host / "hooks" / "link_install.py", "erc2_link_install")
        hook.check_and_install(env)
    except Exception as exc:
        # Installing a panel must never block a student's build.
        warn(f"ERC2 Link check failed ({exc}); continuing with the build.")


env.AddPreAction("buildprog", _pre_build)  # noqa: F821
