# -*- coding: utf-8 -*-
#
# Developer mode stops this script from overwriting local files.
#
# Turn it on by creating an empty file named .erc2-dev in the project root, or
# by setting ERC2_TEMPLATE_DEV=1 -- NOT by editing the flag below. This script
# is itself one of the synced files, so a flag edited here is replaced by the
# published copy on the very next build, taking every other local change with
# it. A marker file is outside the sync, so it survives.
#
#     touch .erc2-dev
#
# Developers also point platformio.ini at a local library checkout:
# lib_deps =
#    symlink://../erc2-firmware/firmware/library/
DEVELOPER_MODE = False

#: Presence of this file in the project root enables developer mode.
DEV_MARKER_FILE = ".erc2-dev"

#: Setting this to "1" enables developer mode.
DEV_ENV_VAR = "ERC2_TEMPLATE_DEV"

import hashlib
import json
import os
import ssl
import sys
import time
import urllib.request
from pathlib import Path

# =========================
# CONFIG
# =========================

BASE_RAW_URL = "https://code.osu.edu/fehelectronics/eed_controller/erc2-template/-/raw/main/"

# manifest
MANIFEST_URL = BASE_RAW_URL + "scripts/sync/manifest.json"

# Where to place downloaded files (relative to project root)
DEST_ROOT_REL = "."

# Path blocklist for safety: disallow updating files with these prefixes (relative paths)
DISALLOWED_PREFIXES = (
    ".pio", # PlatformIO build artifacts
    "src", # source code written by students
)

# Network timeouts / behavior
HTTP_TIMEOUT_SEC = 3.0
FAIL_OPEN_IF_OFFLINE = True   # if offline, continue build using local files
RETRY_COUNT = 2               # small retry for flaky WiFi
RETRY_BACKOFF_SEC = 0.25


# =========================
# HELPERS
# =========================

def log(msg: str):
    print(f"\033[96m[ERC2-BOOTSTRAP]\033[0m {msg}")

def _project_root() -> Path:
    """
    Best-effort find PlatformIO project root.

    This script lives at <root>/scripts/sync/bootstrap.py, so walk up until
    we find the directory holding platformio.ini rather than assuming a fixed
    depth -- moving this file then cannot silently resolve to the wrong root.
    """
    try:
        here = Path(__file__).resolve()
        for candidate in here.parents:
            if (candidate / "platformio.ini").is_file():
                return candidate
    except NameError:
        # SCons may exec this script without defining __file__
        pass

    # fallback: current working dir (PlatformIO runs from the project root)
    return Path.cwd().resolve()


def _normalize_relpath(rel: str) -> str:
    # Normalize separators and remove a leading "./" (str.lstrip is
    # character-based and would eat the dot of paths like ".vscode/...")
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    return rel


def _is_safe_relpath(rel: str) -> bool:
    rel = _normalize_relpath(rel)

    # Disallow absolute paths, parent traversal, or empty
    if not rel or rel.startswith("/") or rel.startswith("..") or "/../" in rel:
        return False

    # Block disallowed prefixes
    if DISALLOWED_PREFIXES:
        if any(rel.startswith(p) for p in DISALLOWED_PREFIXES):
            return False
    
    return True


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        # Read entire file (these are small text files) and normalize CRLF to LF
        content = f.read().replace(b"\r\n", b"\n")
        h.update(content)
    return h.hexdigest()


def _tls_context() -> ssl.SSLContext:
    """Verified TLS, with PlatformIO's CA bundle when the system has none.

    What this script downloads, PlatformIO runs: platformio.ini and the
    scripts it names. Unverified, anyone who could answer for the template's
    host on a campus network could run code on every student's machine.
    Python from python.org on macOS ships without system certificates, but
    PlatformIO's Python carries certifi. If verification still fails, the
    download fails, and the build goes on with the local files.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _http_get_bytes(url: str) -> bytes:
    ctx = _tls_context()

    last_err = None
    for i in range(RETRY_COUNT + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "erc2-bootstrap/1.0"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC, context=ctx) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            if i < RETRY_COUNT:
                time.sleep(RETRY_BACKOFF_SEC * (2 ** i))
    raise last_err  # type: ignore


def _parse_manifest(manifest_text: str):
    """
    JSON format with array of file objects, and the files no longer synced:
    {
      "files": [
        {"path": "...", "sha256": "..."},
        ...
      ],
      "removed": ["...", ...]
    }

    Returns (rows, removed).
    """
    try:
        data = json.loads(manifest_text)
        rows = []
        removed = []
        if isinstance(data, dict) and "files" in data:
            for file_obj in data.get("files", []):
                if isinstance(file_obj, dict) and "path" in file_obj and "sha256" in file_obj:
                    rel_path = file_obj["path"].strip().replace("\\", "/")
                    sha256 = file_obj["sha256"].strip()
                    if rel_path and not rel_path.startswith("#"):
                        rows.append((rel_path, sha256))
        if isinstance(data, dict):
            removed = [p for p in data.get("removed", []) if isinstance(p, str) and p.strip()]
        return rows, removed
    except json.JSONDecodeError as e:
        log(f"JSON parse error: {e}")
        return [], []


def _write_atomic(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _retire(root: Path, removed) -> int:
    """Delete files the template used to sync and no longer does.

    Without this, a file dropped from the template stayed in every student's
    project for good -- a VS Code task for a tool that no longer exists, say.

    A file the platformio.ini this build was started with still names is left
    for the next build: PlatformIO has already read that ini and will look for
    it. By then the ini is the template's new one, which does not.
    """
    try:
        ini = (root / "platformio.ini").read_text(encoding="utf-8", errors="replace")
    except OSError:
        ini = ""
    count = 0
    for relpath in removed:
        rel = _normalize_relpath(relpath)
        if not _is_safe_relpath(rel) or rel in ini:
            continue
        path = (root / rel).resolve()
        if not str(path).startswith(str(root)) or not path.is_file():
            continue
        try:
            path.unlink()
            count += 1
            log(f"Removed: {rel}")
        except OSError as e:
            log(f"FAILED to remove {rel}: {e}")
    return count


def sync_files():
    root = _project_root()
    dest_root = (root / DEST_ROOT_REL).resolve()

    if DEVELOPER_MODE:
        log("developer mode enabled, skipping sync.")
        return

    if os.environ.get(DEV_ENV_VAR) == "1":
        log(f"{DEV_ENV_VAR}=1 — developer mode, skipping sync.")
        return

    if (root / DEV_MARKER_FILE).exists():
        log(f"{DEV_MARKER_FILE} present — developer mode, skipping sync.")
        return

    log(f"checking updates via {MANIFEST_URL}")

    try:
        manifest_bytes = _http_get_bytes(MANIFEST_URL)
    except Exception as e:
        log(f"manifest download failed: {e}")
        if FAIL_OPEN_IF_OFFLINE:
            log("continuing with local files (offline mode).")
            return
        raise

    rows, removed = _parse_manifest(manifest_bytes.decode("utf-8", errors="replace"))
    retired = _retire(root, removed)
    if not rows:
        log("manifest empty; nothing to do.")
        return

    updated = 0
    skipped = 0

    for relpath, expected in rows:
        relpath_norm = _normalize_relpath(relpath)

        if not _is_safe_relpath(relpath_norm):
            log(f"SKIP unsafe path in manifest: {relpath_norm}")
            skipped += 1
            continue

        local_path = (dest_root / relpath_norm).resolve()

        # Ensure local path is still within project root (extra safety)
        if not str(local_path).startswith(str(root)):
            log(f"SKIP path escapes project root: {relpath_norm}")
            skipped += 1
            continue

        remote_url = BASE_RAW_URL + relpath_norm

        needs_update = True
        if local_path.exists():
            # JSON manifest always provides sha256
            local_hash = _sha256_file(local_path)
            needs_update = (local_hash.lower() != expected.lower())

        if not needs_update:
            continue

        try:
            data = _http_get_bytes(remote_url)
            _write_atomic(local_path, data)
            updated += 1
            log(f"Updated: {relpath_norm}")
        except Exception as e:
            log(f"FAILED to update {relpath_norm}: {e}")
            if not FAIL_OPEN_IF_OFFLINE:
                raise

    if updated == 0 and skipped == 0 and retired == 0:
        log("already up to date.")
    else:
        log(f"done (updated={updated}, removed={retired}, skipped={skipped}).")

# Run immediately when PlatformIO imports this script
sync_files()