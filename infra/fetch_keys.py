#!/usr/bin/env python3
"""Import missing public SSH keys from an existing host's authorized_keys.

Usage: infra/fetch_keys.py [HOST]   (default: repairnator, needs passwordless sudo there)

Only fills infra/ssh-keys/<login>.pub files that do not exist yet; never overwrites.
Key options (expiry-time=..., restrict, ...) are stripped: they are deployment policy.
"""
from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KEYS = ROOT / "infra" / "ssh-keys"
KEY_RE = re.compile(r"((?:ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp\d+|sk-ssh-ed25519@openssh\.com|sk-ecdsa-sha2-nistp256@openssh\.com) [A-Za-z0-9+/=]+(?: .*)?)$")


def main() -> int:
    host = sys.argv[1] if len(sys.argv) > 1 else "repairnator"
    people = yaml.safe_load((ROOT / "_data" / "people.yml").read_text())
    KEYS.mkdir(parents=True, exist_ok=True)
    for pid, p in people.items():
        login = p.get("unix_login")
        if str(p.get("role", "")).endswith("alum") or not login or (KEYS / f"{login}.pub").exists():
            continue
        cmd = f"sudo -n cat /home/{shlex.quote(login)}/.ssh/authorized_keys"
        out = subprocess.run(["ssh", "-o", "BatchMode=yes", host, cmd], capture_output=True, text=True).stdout
        keys = []
        for line in out.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = KEY_RE.search(line)
            if m and m.group(1) not in keys:
                keys.append(m.group(1))
        if keys:
            (KEYS / f"{login}.pub").write_text("\n".join(keys) + "\n")
            print(f"✅ {pid} ({login}): {len(keys)} key(s) from {host}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
