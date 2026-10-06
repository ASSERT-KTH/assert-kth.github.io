# Team infrastructure as code

Every current team member (role not ending in `alum`) in `_data/people.yml` must have:

1. a `unix_login` field in `_data/people.yml`
2. at least one public SSH key in `infra/ssh-keys/<unix_login>.pub` (authorized_keys format, one key per line, no options)

```
infra/check.py               # silent + exit 0 when complete; lists what is missing otherwise
infra/fetch_keys.py [HOST]   # import missing key files from HOST's authorized_keys (default: repairnator)
```

To add a member: add `unix_login` to their entry, add `infra/ssh-keys/<login>.pub`, run `infra/check.py`.
