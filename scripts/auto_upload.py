# -*- coding: utf-8 -*-
"""
Auto-upload watcher — auto_upload.py

Watches the serial ports and runs ``pio run -t upload`` every time a new
Arduino board shows up.  Plug a board in, it gets flashed; unplug it, plug in
the next one, it gets flashed too.  Useful for programming a pile of boards
without touching the keyboard between them.

This is *not* a PlatformIO extra_script — it drives PlatformIO, so running it
from platformio.ini would recurse.  Run it yourself, in its own terminal:

    python scripts/auto_upload.py                 # watch forever
    python scripts/auto_upload.py --env megaatmega2560
    python scripts/auto_upload.py --any           # don't filter by USB vendor
    python scripts/auto_upload.py --once          # flash one board, then exit

Stop it with Ctrl-C.

Notes
-----
* Uploading resets the board, and many USB-serial bridges drop off the bus
  while that happens.  Ports are therefore put on a cooldown after a flash so
  the reappearing port is not treated as a brand new board.
* Ports present at startup are treated as already-known, so nothing is
  flashed until you actually plug something in.  Pass --flash-existing to
  flash whatever is already connected first.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

import serial.tools.list_ports

# USB vendor IDs that mean "this is probably an Arduino-compatible board".
# Arduino LLC/SA, plus the usual clone bridges (CH340, CP210x, FTDI, PL2303).
ARDUINO_VIDS = {
    0x2341,  # Arduino LLC
    0x2A03,  # Arduino SRL
    0x2E8A,  # Raspberry Pi (Pico-class boards)
    0x1B4F,  # SparkFun
    0x239A,  # Adafruit
    0x1A86,  # QinHeng CH340/CH341
    0x10C4,  # Silicon Labs CP210x
    0x0403,  # FTDI
    0x067B,  # Prolific PL2303
}

# How often to re-list the ports
POLL_INTERVAL_SEC = 1.0

# Let the USB device finish enumerating before avrdude opens it
SETTLE_TIME_SEC = 1.5

# Ignore a port for this long after we flashed it, so the reset-induced
# re-enumeration doesn't look like a newly connected board
COOLDOWN_SEC = 10.0


def _log(msg: str) -> None:
    print(f"\033[96m[AUTO-UPLOAD]\033[0m {msg}", flush=True)


def _is_arduino(port) -> bool:
    """True if *port* looks like an Arduino-compatible board."""
    return port.vid in ARDUINO_VIDS


def _scan(match_any: bool) -> dict:
    """Map of device name -> description for every port we care about."""
    return {
        p.device: (p.description or p.device)
        for p in serial.tools.list_ports.comports()
        if match_any or _is_arduino(p)
    }


def _upload(port: str, env: str | None) -> bool:
    """Run ``pio run -t upload`` against *port*.  True if it succeeded."""
    cmd = [sys.executable, "-m", "platformio", "run", "-t", "upload",
           "--upload-port", port]
    if env:
        cmd += ["-e", env]

    _log(f"Uploading to {port} …")
    result = subprocess.run(cmd)
    if result.returncode == 0:
        _log(f"\033[92mUpload to {port} succeeded.\033[0m")
        return True
    _log(f"\033[91mUpload to {port} failed (exit {result.returncode}).\033[0m")
    return False


def watch(env: str | None, match_any: bool, once: bool,
          flash_existing: bool) -> int:
    known = {} if flash_existing else _scan(match_any)
    cooldown: dict[str, float] = {}

    if known:
        _log(f"Ignoring already-connected port(s): {', '.join(sorted(known))}")
    _log("Waiting for a board to be plugged in…  (Ctrl-C to stop)")

    while True:
        current = _scan(match_any)

        # Drop cooldowns for ports that went away, and forget vanished ports.
        for port in list(known):
            if port not in current:
                _log(f"{port} disconnected.")
                known.pop(port, None)
        cooldown = {p: t for p, t in cooldown.items() if p in current}

        for port, description in current.items():
            if port in known:
                continue
            if time.monotonic() < cooldown.get(port, 0.0):
                # Same board coming back from its post-upload reset.
                known[port] = description
                continue

            _log(f"New board detected on {port} ({description}).")
            time.sleep(SETTLE_TIME_SEC)

            known[port] = description
            _upload(port, env)
            cooldown[port] = time.monotonic() + COOLDOWN_SEC

            if once:
                return 0
            _log("Waiting for the next board…")

        time.sleep(POLL_INTERVAL_SEC)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 'pio run -t upload' whenever a new Arduino is plugged in."
    )
    parser.add_argument("-e", "--env", help="PlatformIO environment to build")
    parser.add_argument("--any", dest="match_any", action="store_true",
                        help="react to any new serial port, not just known "
                             "Arduino-compatible USB vendors")
    parser.add_argument("--once", action="store_true",
                        help="exit after the first board is flashed")
    parser.add_argument("--flash-existing", action="store_true",
                        help="also flash boards already connected at startup")
    args = parser.parse_args()

    try:
        return watch(args.env, args.match_any, args.once, args.flash_existing)
    except KeyboardInterrupt:
        _log("Stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
