#!/usr/bin/env python3
"""SDDM autologin consolidator — run via pkexec for root privileges."""

import re
import shutil
import sys
from pathlib import Path

SDDM_CONF = Path("/etc/sddm.conf")
SDDM_CONF_D = Path("/etc/sddm.conf.d")
MANAGED_FILE = SDDM_CONF_D / "dms-mango-autologin.conf"


def find_autologin_files() -> list[Path]:
    paths: list[Path] = []
    if SDDM_CONF.exists() and "[Autologin]" in SDDM_CONF.read_text(errors="ignore"):
        paths.append(SDDM_CONF)
    if SDDM_CONF_D.exists():
        for p in sorted(SDDM_CONF_D.glob("*.conf")):
            if "[Autologin]" in p.read_text(errors="ignore"):
                paths.append(p)
    return paths


def strip_autologin(path: Path, backup_dir: Path) -> None:
    text = path.read_text(errors="ignore")
    if "[Autologin]" not in text:
        return
    backup = backup_dir / path.relative_to(Path("/"))
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup)
    # Strip [Autologin] section
    cleaned = re.sub(r"(?ms)^\[Autologin\]\s*.*?^(?=\[|\Z)", "", text, count=1)
    # Clean up extra blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    path.write_text(cleaned)
    print(f"Backed up and stripped [Autologin] from {path}")


def write_managed(user: str, session: str, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    # Strip from all existing files
    for path in find_autologin_files():
        strip_autologin(path, backup_dir)
    # Write managed file
    content = (
        "[Autologin]\n"
        f"Relogin=false\n"
        f"Session={session}\n"
        f"User={user}\n"
    )
    MANAGED_FILE.write_text(content)
    print(f"Wrote {MANAGED_FILE}")


def remove_managed(backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    if MANAGED_FILE.exists():
        backup = backup_dir / MANAGED_FILE.relative_to(Path("/"))
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MANAGED_FILE, backup)
        MANAGED_FILE.unlink()
        print(f"Removed {MANAGED_FILE}")
    # Also strip from any other files as safety
    for path in find_autologin_files():
        strip_autologin(path, backup_dir)
    print("Autologin disabled.")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: sddm-consolidate-autologin.py write <user> <session> <backup_dir>")
        print("       sddm-consolidate-autologin.py remove <backup_dir>")
        return 2

    cmd = sys.argv[1]
    if cmd == "write":
        if len(sys.argv) < 5:
            print("Usage: write <user> <session> <backup_dir>")
            return 2
        user, session, backup_dir = sys.argv[2], sys.argv[3], Path(sys.argv[4])
        write_managed(user, session, backup_dir)
        return 0
    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("Usage: remove <backup_dir>")
            return 2
        backup_dir = Path(sys.argv[2])
        remove_managed(backup_dir)
        return 0
    else:
        print(f"Unknown command: {cmd}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
