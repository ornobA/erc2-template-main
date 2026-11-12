# -*- coding: utf-8 -*-
"""
Rebuild scripts/sync/manifest.json from what is actually in this project.

The manifest tells bootstrap.py which skeleton files to keep in sync with the
template. It used to be a hand-maintained list that this script merely
re-hashed: a file added here never reached students, and a file deleted here
left an entry pointing at a URL that 404s. So it now rescans the tree, and the
list cannot drift from it.

Student code is never synced -- ``src/`` is excluded, matching bootstrap's own
blocklist -- and neither is the manifest itself, which bootstrap fetches
separately.

A file that leaves the template is listed under "removed", and bootstrap
deletes it from students' projects. The list only grows: a student who last
built a year ago still has every file retired since.

    python scripts/sync/update_manifest.py
"""

import hashlib
import json
import subprocess
from pathlib import Path

#: Never synced. src/ is the student's own work; .pio is build output.
EXCLUDED_PREFIXES = ("src/", ".pio/")

#: Fetched separately by bootstrap, so it must not list itself.
EXCLUDED_PATHS = {"scripts/sync/manifest.json"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        # Read entire file and normalize CRLF to LF
        content = f.read().replace(b"\r\n", b"\n")
        h.update(content)
    return h.hexdigest().upper()


def tracked_files(root: Path) -> list[str]:
    """Every file git tracks, as project-relative POSIX paths."""
    out = subprocess.check_output(["git", "ls-files"], cwd=root, text=True)
    return sorted(line.strip() for line in out.splitlines() if line.strip())


def should_sync(rel_path: str) -> bool:
    if rel_path in EXCLUDED_PATHS:
        return False
    return not any(rel_path.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / "scripts" / "sync" / "manifest.json"

    try:
        candidates = tracked_files(root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERC2] not a git checkout; cannot rebuild the manifest.")
        return

    previous = {}
    removed_before = set()
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        previous = {e["path"]: e.get("sha256") for e in data.get("files", [])}
        removed_before = set(data.get("removed", []))

    files = []
    for rel_path in candidates:
        if not should_sync(rel_path):
            continue
        path = root / rel_path
        if not path.is_file():
            continue
        files.append({"path": rel_path, "sha256": sha256_file(path)})

    now = {entry["path"] for entry in files}
    for added in sorted(now - set(previous)):
        print(f"[ERC2] + {added}")
    for removed in sorted(set(previous) - now):
        print(f"[ERC2] - {removed}")
    for entry in files:
        if entry["path"] in previous and previous[entry["path"]] != entry["sha256"]:
            print(f"[ERC2] ~ {entry['path']}")

    # A file that comes back is synced again, not deleted.
    removed = sorted((removed_before | (set(previous) - now)) - now)

    with manifest_path.open("w", newline="\n", encoding="utf-8") as f:
        json.dump({"files": files, "removed": removed}, f, indent=4)
        f.write("\n")

    # Stage it so it lands in the same commit as the change that prompted it.
    subprocess.run(["git", "add", "scripts/sync/manifest.json"], cwd=root)
    print(f"[ERC2] manifest.json rebuilt: {len(files)} files.")


if __name__ == "__main__":
    main()
