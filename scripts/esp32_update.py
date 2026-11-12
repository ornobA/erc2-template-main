# -*- coding: utf-8 -*-
"""
PlatformIO upload hook — keeps the ERC2's ESP32 co-processor up to date.

This is a stub. The hook itself ships inside the ERC2 library package
(``bin/host/hooks/esp32_update.py``), so it stays in step with the firmware
and the protocol it flashes; this file only finds it and hands over.

The work happens as a pre-upload action, by which point PlatformIO has
installed the library -- so the lookup always succeeds even on a first build
of a fresh checkout, where libdeps do not exist yet at config time.

Environment overrides (for testing and troubleshooting):
    ERC2_ESP32=skip     never touch the ESP32
    ERC2_ESP32=force    reflash even when the build already matches
    ERC2_ESP32=dry-run  report what would happen, but do not flash
"""

import sys
from pathlib import Path

Import("env")  # noqa: F821 — injected by PlatformIO

PROJECT_DIR = Path(env.subst("$PROJECT_DIR")).resolve()  # noqa: F821
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from _erc2_package import find_host_dir, load_module, warn  # noqa: E402


def _pre_upload(target, source, env) -> None:
    try:
        host = find_host_dir(env.subst("$PROJECT_LIBDEPS_DIR"), env.subst("$PIOENV"))
        if host is None:
            warn("ERC2 library tooling not found; skipping the ESP32 check.")
            return
        hook = load_module(host / "hooks" / "esp32_update.py", "erc2_esp32_update")
        hook.check_and_update(env)
    except Exception as exc:
        # An ESP32 problem must never block a student's upload.
        warn(f"ESP32 check failed ({exc}); continuing with the upload.")


env.AddPreAction("upload", _pre_upload)  # noqa: F821
