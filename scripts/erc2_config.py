# -*- coding: utf-8 -*-
"""Report which ERC2 features this build switched off, and act on two of them.

The switches themselves live in `src/erc2_config.h` and are read by the
compiler, not by this script -- see firmware/library/include/ERC2Config.h in the
firmware repo. Everything here is either something the preprocessor cannot
reach or something a student should be told:

  * **The banner.** A config file is easy to copy from a friend and forget
    about, and a board that has quietly stopped answering ERC2 Link is a bad
    afternoon. So every build says what is off.

  * **A stale package.** The switches only reach a precompiled library
    because the package ships one archive per combination and picks between
    them (bin/variants/, bin/select_variant.py). A package from before that
    existed would link the full build and free nothing, silently, so that case
    is named rather than left to be discovered from a RAM figure that did not
    move.

  * **The UART buffers.** `SERIAL_RX_BUFFER_SIZE` is read by the Arduino core
    when HardwareSerial.cpp is compiled, which a header in the library cannot
    reach -- it has to be a build flag. They are large because a whole link
    packet must fit in them, so a build with no link does not need them and
    gets 384 bytes of SRAM back.

If this script and the compiler ever disagree about what is switched off -- a
#define hidden behind an #if, say -- the compiler wins, and the static_assert
in agent/transport_usb.cpp catches the one case that matters by failing the
build rather than shipping a link with buffers too small to work.
"""

import json
import re
from pathlib import Path

Import("env")

CONFIG_REL = "src/erc2_config.h"

#: Stock AVR core sizes, which is what a build with no link needs.
STOCK_SERIAL_BUFFER = 64

#: Switch -> what a student loses by setting it. Kept here rather than derived,
#: because the point of the banner is to name the consequence, not the macro.
FEATURES = {
    "ERC2_DISABLE_LINK": "ERC2 Link entirely (logs, file browser, LCD mirror, over USB and Bluetooth)",
    "ERC2_DISABLE_BLUETOOTH": "ERC2 Link over Bluetooth (the USB cable still works)",
    "ERC2_DISABLE_LCD_MIRROR": "the LCD mirror in ERC2 Link",
    "ERC2_DISABLE_SD": "the SD card (FEHSD, FEHFile, and the file browser)",
}

#: A #define on a line of its own, ignoring commented-out examples.
DEFINE_RE = re.compile(r"^\s*#\s*define\s+(ERC2_DISABLE_[A-Z0-9_]+)\b", re.M)


def _strip_comments(text):
    """Drop /* */ and // so a commented-out example does not read as a switch."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def _disabled_features(project_dir):
    config = Path(project_dir) / CONFIG_REL
    if not config.is_file():
        return []
    try:
        text = _strip_comments(config.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []
    # dict.fromkeys: first-seen order, no duplicates.
    return list(dict.fromkeys(DEFINE_RE.findall(text)))


def _report(disabled, unknown):
    print("")
    if disabled:
        print("[ERC2-CONFIG] Switched off in %s:" % CONFIG_REL)
        for name in disabled:
            print("[ERC2-CONFIG]   %-24s disables %s" % (name, FEATURES[name]))
    if "ERC2_DISABLE_LINK" in disabled:
        print("[ERC2-CONFIG]   UART buffers back to %d bytes; ERC2 Link will not "
              "connect to this board." % STOCK_SERIAL_BUFFER)
    if "ERC2_DISABLE_SD" in disabled:
        # The compiler cannot name the switch here: erc2.h simply stops
        # declaring SD and File, so a program still using them fails with
        # "was not declared" and no hint as to why. Say it in advance.
        print("[ERC2-CONFIG]   If the build now fails with \"'SD' was not "
              "declared\" or \"'File' was not declared\",")
        print("[ERC2-CONFIG]   that is this switch, not a mistake in your code.")
    for name in unknown:
        print("[ERC2-CONFIG] %s is not an ERC2 switch -- check the spelling "
              "against the" % name)
        print("[ERC2-CONFIG]   names in %s. It is doing nothing." % CONFIG_REL)
    if disabled:
        print("[ERC2-CONFIG] Put the // back in front of a line to get that "
              "feature back.")
    print("")


def _installed_erc2(project_dir, pioenv):
    """Where the ERC2 library this build will use actually lives, or None.

    Two shapes to cope with. A registry install is a directory named after the
    package; a `symlink://` dependency -- what a developer uses -- is a small
    .pio-link file naming the real path instead. Both are searched rather than
    assuming one, because the warning below is worth nothing if it only fires
    in the case that never goes wrong.
    """
    libdeps = Path(project_dir) / ".pio" / "libdeps" / pioenv
    if not libdeps.is_dir():
        return None

    candidates = []
    for entry in libdeps.iterdir():
        if entry.is_dir():
            candidates.append(entry)
        elif entry.suffix == ".pio-link":
            try:
                uri = json.loads(entry.read_text())["spec"]["uri"]
            except (OSError, ValueError, KeyError, TypeError):
                continue
            if uri.startswith("symlink://"):
                target = Path(uri[len("symlink://"):])
                if not target.is_absolute():
                    target = Path(project_dir) / target
                candidates.append(target)

    for path in candidates:
        try:
            manifest = json.loads((path / "library.json").read_text())
        except (OSError, ValueError):
            continue
        if manifest.get("name") == "ERC2":
            return path
    return None


def _stale_package_warning():
    """A precompiled ERC2 that predates the per-variant archives.

    Returns a reason string, or None when the package can honour the switches
    (or when the library is built from source, where they always work).
    """
    lib = _installed_erc2(env.subst("$PROJECT_DIR"), env.subst("$PIOENV"))
    if lib is None:
        # First build of a fresh project: the dependency is installed after
        # this hook runs, so there is nothing to inspect yet. The next build
        # will look.
        return None
    if (lib / "src").is_dir():
        return None                      # built from source; nothing to select
    if not (lib / "bin" / "libERC2.a").is_file():
        return None                      # not a shape we know; leave it be
    if (lib / "bin" / "variants").is_dir():
        return None                      # can select
    return ("the installed ERC2 library predates the per-variant builds, so it "
            "cannot honour these switches")


found = _disabled_features(env.subst("$PROJECT_DIR"))
disabled = [name for name in found if name in FEATURES]
unknown = [name for name in found if name not in FEATURES]

if found:
    _report(disabled, unknown)

if disabled:
    stale = _stale_package_warning()
    if stale:
        print("[ERC2-CONFIG] WARNING: %s." % stale)
        print("[ERC2-CONFIG] The build will succeed and free nothing. Update "
              "the ERC2 library to a")
        print("[ERC2-CONFIG] version that ships bin/variants/, or remove the "
              "switches.")
        print("")

if "ERC2_DISABLE_LINK" in disabled:
    # Drop the link-sized buffers the template sets, and put the stock ones back.
    kept = [
        flag for flag in env["BUILD_FLAGS"]
        if not str(flag).startswith(("-DSERIAL_RX_BUFFER_SIZE",
                                     "-DSERIAL_TX_BUFFER_SIZE"))
    ]
    env.Replace(BUILD_FLAGS=kept)
    env.Append(CPPDEFINES=[
        ("SERIAL_RX_BUFFER_SIZE", STOCK_SERIAL_BUFFER),
        ("SERIAL_TX_BUFFER_SIZE", STOCK_SERIAL_BUFFER),
    ])
