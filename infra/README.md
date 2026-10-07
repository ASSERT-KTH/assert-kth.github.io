# Team infrastructure as code

Every current team member (role not ending in `alum`) in `_data/people.yml` must have:

1. a `unix_login` field in `_data/people.yml`
2. at least one public SSH key in `infra/ssh-keys/<unix_login>.pub` (authorized_keys format, one key per line, no options)

```
infra/check.py               # silent + exit 0 when complete; lists what is missing otherwise (also checks roles and images)
infra/check.py --allow-missing-keys  # what CI runs on every PR (.github/workflows/ci.yml): missing keys don't fail
infra/fetch_keys.py [HOST]   # import missing key files from HOST's authorized_keys (default: repairnator)
infra/test_sync.sh           # end-to-end test of sync_users.py in a docker container with real sshd
infra/deploy.sh HOST [--enable]  # install the sync on HOST; --enable starts the 15 min timer
```

To add a member: add `unix_login` to their entry, add `infra/ssh-keys/<login>.pub`, run `infra/check.py`, push.

## Server-side sync (`sync_users.py`, installed as `/usr/local/sbin/assert-sync-users`)

A systemd timer pulls this repo from GitHub (master) into `/var/lib/assert-users/repo` every 15 minutes, then as root:

- creates missing member accounts (bash, docker group), re-enables expired ones
- overwrites each member's `~/.ssh/authorized_keys` with the config (keys added by hand are removed)
- disables (account expiry, nothing deleted) every other local account with uid 1000–59999

Undo a disable by hand: `usermod --expiredate '' LOGIN`.

Dry-run: `sudo assert-sync-users /var/lib/assert-users/repo --dry-run`

### Escape hatches

- `ssh root@HOST` with the admin key: `/root/.ssh/authorized_keys` is never touched by the sync
- `touch /etc/assert-users/disabled`: the sync does nothing until the file is removed
- `/etc/assert-users/protected` (installed from `infra/protected` by `deploy.sh`): logins the sync never modifies
- the sync aborts without changes if the config is invalid or the admin (`martin`) has no key
