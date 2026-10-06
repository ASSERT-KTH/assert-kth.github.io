#!/bin/sh
# End-to-end test of sync_users.py in a throwaway Ubuntu 24.04 container with a real sshd.
# Usage: infra/test_sync.sh   (needs docker; prints PASS/FAIL lines, exit 1 on any failure)
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
exec docker run --rm -i --dns 1.1.1.1 -v "$DIR/sync_users.py:/sync.py:ro" ubuntu:24.04 sh -s <<'EOF'
set -u
apt-get -qq update >/dev/null 2>&1; apt-get -qq install -y python3-yaml openssh-server openssh-client >/dev/null 2>&1
command -v python3 >/dev/null && command -v sshd >/dev/null || { echo "FAIL setup: packages missing"; exit 1; }
sed -i 's/^#\?Port 22$/Port 2222/' /etc/ssh/sshd_config
mkdir -p /run/sshd && ssh-keygen -A >/dev/null && /usr/sbin/sshd
FAIL=0
ok() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; FAIL=1; fi; }
key() { [ -f /k/$1 ] || ssh-keygen -q -t ed25519 -N '' -C $1 -f /k/$1; cat /k/$1.pub; }
canlogin() { ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p 2222 -i /k/$2 $1@localhost true 2>/dev/null; }
mkdir -p /k /cfg/_data /cfg/infra/ssh-keys /root/.ssh
groupadd docker
key martin >/dev/null; key alice >/dev/null; key carol >/dev/null; key dave >/dev/null; key bob >/dev/null; key old >/dev/null
cat > /cfg/_data/people.yml <<Y
martin: {display_name: "Martin M", role: faculty, unix_login: martin}
alice: {display_name: "Alice", role: grad, unix_login: alice}
carol: {display_name: "Carol", role: grad, unix_login: carol}
dave: {display_name: "Dave", role: postdoc, unix_login: dave}
erin: {display_name: "Erin", role: grad, unix_login: erin}
bob: {display_name: "Bob", role: alum, unix_login: bob}
Y
for u in martin alice carol dave; do cat /k/$u.pub > /cfg/infra/ssh-keys/$u.pub; done
key erin >/dev/null; cat /k/erin.pub > /cfg/infra/ssh-keys/erin.pub
useradd -M -s /bin/bash erin   # existing account without home dir (seen on repairnator)
# initial machine state
for u in martin alice bob dave svc; do useradd -m -s /bin/bash $u; done
mkdir -p /home/alice/.ssh && cat /k/old.pub > /home/alice/.ssh/authorized_keys && chown -R alice /home/alice/.ssh
mkdir -p /home/bob/.ssh && cat /k/bob.pub > /home/bob/.ssh/authorized_keys && chown -R bob /home/bob/.ssh
usermod --expiredate 1 dave
mkdir -p /etc/assert-users && echo svc > /etc/assert-users/protected
cat /k/martin.pub > /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys
ROOTKEYS=$(md5sum < /root/.ssh/authorized_keys)
ok "bob can log in before sync" "canlogin bob bob"

OUT=$(python3 /sync.py /cfg --dry-run)
ok "dry-run lists changes" "echo '$OUT' | grep -q 'dry-run.*disabled bob'"
ok "dry-run changes nothing" "canlogin bob bob && ! id carol >/dev/null 2>&1"

OUT=$(python3 /sync.py /cfg); echo "$OUT"
ok "carol created" "id carol >/dev/null 2>&1"
ok "carol in docker" "id -nG carol | grep -qw docker"
ok "carol can log in" "canlogin carol carol"
ok "dave re-enabled, can log in" "canlogin dave dave"
ok "alice new key works" "canlogin alice alice"
ok "alice old key removed" "! canlogin alice old"
ok "bob (alum) disabled" "! canlogin bob bob"
ok "bob home kept" "test -f /home/bob/.ssh/authorized_keys"
ok "svc (protected) untouched" "! echo '$OUT' | grep -q svc"
ok "martin can log in" "canlogin martin martin"
ok "erin (no home) gets home + can log in" "test -d /home/erin && canlogin erin erin"
ok "root keys untouched" "[ \"\$(md5sum < /root/.ssh/authorized_keys)\" = '$ROOTKEYS' ]"
ok "escape hatch: root login with admin key" "canlogin root martin"
ok "second run silent" "[ -z \"\$(python3 /sync.py /cfg)\" ]"

rm /cfg/infra/ssh-keys/martin.pub
python3 /sync.py /cfg 2>/dev/null; RC=$?
ok "no admin key -> abort rc=1" "[ $RC = 1 ]"
ok "abort changed nothing" "canlogin alice alice"
cat /k/martin.pub > /cfg/infra/ssh-keys/martin.pub

echo "garbage" >> /cfg/infra/ssh-keys/alice.pub
python3 /sync.py /cfg 2>/dev/null; RC=$?
ok "malformed key -> abort rc=1" "[ $RC = 1 ]"
cat /k/alice.pub > /cfg/infra/ssh-keys/alice.pub

sed -i 's/role: grad, unix_login: alice/role: alum, unix_login: alice/' /cfg/_data/people.yml
touch /etc/assert-users/disabled
ok "kill switch: silent" "[ -z \"\$(python3 /sync.py /cfg)\" ]"
ok "kill switch: alice still in" "canlogin alice alice"
rm /etc/assert-users/disabled
python3 /sync.py /cfg >/dev/null
ok "alice leaves team -> disabled" "! canlogin alice alice"
sed -i 's/role: alum, unix_login: alice/role: grad, unix_login: alice/' /cfg/_data/people.yml
ok "alice back -> re-enabled msg" "python3 /sync.py /cfg | grep -q 're-enabled alice'"
ok "alice back -> can log in" "canlogin alice alice"
exit $FAIL
EOF
