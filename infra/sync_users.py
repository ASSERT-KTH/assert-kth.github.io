#!/usr/bin/env python3
"""Make local unix accounts match the team config. Runs as root on the server.

Usage: sync_users.py CONFIG_DIR [--dry-run]

CONFIG_DIR is a checkout of this repo (reads _data/people.yml and infra/ssh-keys/).

For every current member (role not ending in "alum") with a unix_login:
  - create the account if missing (bash, home dir, docker group if it exists)
  - re-enable it if expired
  - overwrite ~/.ssh/authorized_keys with infra/ssh-keys/<login>.pub
Every other local account with 1000 <= uid < 60000 is disabled (expiry date set
in the past). Nothing is deleted: homes and keys stay, `usermod --expiredate ''`
restores access.

Escape hatches:
  - /root/.ssh/authorized_keys is never touched (holds the admin's key)
  - touch /etc/assert-users/disabled  -> the script exits without doing anything
  - logins listed in /etc/assert-users/protected are never modified
  - aborts without any change if the config is invalid, or if ADMIN has no key

Silent when nothing changes; prints one line per change otherwise.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

ADMIN = "martin"
ETC = Path(os.environ.get("ASSERT_USERS_ETC", "/etc/assert-users"))
UID_MIN, UID_MAX = 1000, 60000
LOGIN_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
KEY_RE = re.compile(r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp\d+|sk-ssh-ed25519@openssh\.com|sk-ecdsa-sha2-nistp256@openssh\.com) [A-Za-z0-9+/=]+( .*)?$")
MIN_MEMBERS = 3


class ConfigError(Exception):
    pass


def load_config(config_dir: Path) -> dict[str, tuple[str, list[str]]]:
    """Return {login: (display_name, [keys])} for current members."""
    people = yaml.safe_load((config_dir / "_data" / "people.yml").read_text())
    if not isinstance(people, dict):
        raise ConfigError("people.yml is not a mapping")
    members: dict[str, tuple[str, list[str]]] = {}
    for pid, p in people.items():
        if str(p.get("role", "")).endswith("alum") or not p.get("unix_login"):
            continue
        login = p["unix_login"]
        if not LOGIN_RE.match(login) or login == "root":
            raise ConfigError(f"invalid unix_login {login!r} for {pid}")
        if login in members:
            raise ConfigError(f"duplicate unix_login {login!r}")
        keyfile = config_dir / "infra" / "ssh-keys" / f"{login}.pub"
        keys = [l.strip() for l in keyfile.read_text().splitlines() if l.strip() and not l.startswith("#")] if keyfile.exists() else []
        for k in keys:
            if not KEY_RE.match(k):
                raise ConfigError(f"malformed key in {keyfile}")
        name = re.sub(r"[:,\n]", " ", str(p.get("display_name", "")))
        members[login] = (name, keys)
    if not members.get(ADMIN, ("", []))[1]:
        raise ConfigError(f"admin {ADMIN!r} has no key: refusing to run")
    if len(members) < MIN_MEMBERS:
        raise ConfigError(f"only {len(members)} members: refusing to run")
    return members


def local_accounts() -> dict[str, tuple[int, str]]:
    """Local accounts from /etc/passwd only (never LDAP): {login: (uid, home)}."""
    out = {}
    for line in Path("/etc/passwd").read_text().splitlines():
        f = line.split(":")
        if len(f) >= 7:
            out[f[0]] = (int(f[2]), f[5])
    return out


def is_expired(login: str) -> bool:
    for line in Path("/etc/shadow").read_text().splitlines():
        f = line.split(":")
        if f[0] == login and len(f) > 7 and f[7]:
            return int(f[7]) <= int(time.time() // 86400)
    return False


def run(cmd: list[str], dry: bool) -> None:
    if not dry:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def write_keys(home: str, keys: list[str], dry: bool) -> bool:
    content = "".join(k + "\n" for k in keys)
    sshdir = Path(home) / ".ssh"
    ak = sshdir / "authorized_keys"
    try:
        if ak.read_text() == content:
            return False
    except OSError:
        pass
    if dry:
        return True
    st = os.stat(home)
    sshdir.mkdir(mode=0o700, exist_ok=True)
    os.chown(sshdir, st.st_uid, st.st_gid)
    tmp = sshdir / "authorized_keys.assert-sync"
    tmp.write_text(content)
    os.chmod(tmp, 0o600)
    os.chown(tmp, st.st_uid, st.st_gid)
    os.replace(tmp, ak)
    return True


def sync(config_dir: Path, dry: bool) -> list[str]:
    members = load_config(config_dir)
    protected = set()
    pfile = ETC / "protected"
    if pfile.exists():
        protected = {l.strip() for l in pfile.read_text().splitlines() if l.strip() and not l.startswith("#")}
    protected |= {"root", ADMIN}
    accounts = local_accounts()
    has_docker = any(l.startswith("docker:") for l in Path("/etc/group").read_text().splitlines())
    changes: list[str] = []

    for login, (name, keys) in sorted(members.items()):
        if login in protected - {ADMIN}:
            continue
        if login not in accounts:
            cmd = ["useradd", "-m", "-s", "/bin/bash", "-c", name]
            if has_docker:
                cmd += ["-G", "docker"]
            run(cmd + [login], dry)
            changes.append(f"➕ created {login}")
            if dry:
                if keys:
                    changes.append(f"🔑 keys {login} ({len(keys)})")
                continue
            accounts = local_accounts()
        elif is_expired(login):
            run(["usermod", "--expiredate", "", login], dry)
            changes.append(f"✅ re-enabled {login}")
        if write_keys(accounts[login][1], keys, dry):
            changes.append(f"🔑 keys {login} ({len(keys)})")

    for login, (uid, _home) in sorted(accounts.items()):
        if UID_MIN <= uid < UID_MAX and login not in members and login not in protected and not is_expired(login):
            run(["usermod", "--expiredate", "1", login], dry)
            changes.append(f"⛔ disabled {login}")
    return changes


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    if (ETC / "disabled").exists():
        return 0
    if not dry and os.geteuid() != 0:
        print("must run as root", file=sys.stderr)
        return 2
    try:
        changes = sync(Path(args[0]), dry)
    except (ConfigError, yaml.YAMLError) as e:
        print(f"❌ invalid config, nothing changed: {e}", file=sys.stderr)
        return 1
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"❌ aborted mid-run: {e}", file=sys.stderr)
        return 1
    prefix = "[dry-run] " if dry else ""
    for c in changes:
        print(prefix + c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
