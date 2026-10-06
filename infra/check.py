#!/usr/bin/env python3
"""Check that every current team member has a unix login and a public SSH key.

Source of truth:
  - _data/people.yml: `unix_login` field per person
  - infra/ssh-keys/<unix_login>.pub: one public key per line (authorized_keys format, no options)

Alumni (role ending in "alum") are skipped. Prints nothing and exits 0 when all is fine.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KEYS = ROOT / "infra" / "ssh-keys"
LOGIN_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
KEY_RE = re.compile(r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp\d+|sk-ssh-ed25519@openssh\.com|sk-ecdsa-sha2-nistp256@openssh\.com) [A-Za-z0-9+/=]+( .*)?$")


def main() -> int:
    people = yaml.safe_load((ROOT / "_data" / "people.yml").read_text())
    errors: list[str] = []
    logins: dict[str, str] = {}
    for pid, p in people.items():
        if str(p.get("role", "")).endswith("alum"):
            continue
        login = p.get("unix_login")
        if not login:
            errors.append(f"❌ {pid}: missing unix_login")
            continue
        if not LOGIN_RE.match(login):
            errors.append(f"❌ {pid}: invalid unix_login {login!r}")
        if login in logins:
            errors.append(f"❌ {pid}: unix_login {login!r} already used by {logins[login]}")
        logins[login] = pid
        keyfile = KEYS / f"{login}.pub"
        lines = [l for l in keyfile.read_text().splitlines() if l.strip() and not l.startswith("#")] if keyfile.exists() else []
        if not lines:
            errors.append(f"🔑 {pid}: no public key in {keyfile.relative_to(ROOT)}")
        for l in lines:
            if not KEY_RE.match(l):
                errors.append(f"❌ {pid}: malformed key line in {keyfile.relative_to(ROOT)}: {l[:40]}...")
    for f in sorted(KEYS.glob("*.pub")):
        if f.stem not in logins:
            errors.append(f"⚠️  orphan key file {f.relative_to(ROOT)} (no current member with this login)")
    for e in errors:
        print(e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
