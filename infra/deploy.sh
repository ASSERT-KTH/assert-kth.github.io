#!/bin/sh
# Install the user sync on HOST (needs passwordless sudo there).
# Usage: infra/deploy.sh HOST [--enable]
#   without --enable: installs everything but leaves the timer off (run a dry-run first)
set -eu
HOST=$1
ENABLE=${2:-}
DIR=$(cd "$(dirname "$0")" && pwd)
REPO=https://github.com/ASSERT-KTH/assert-kth.github.io.git

scp -q "$DIR/sync_users.py" "$DIR/assert-sync-users.service" "$DIR/assert-sync-users.timer" "$DIR/ssh-keys/martin.pub" "$HOST:/tmp/"
ssh "$HOST" "set -eu
sudo install -m 755 /tmp/sync_users.py /usr/local/sbin/assert-sync-users
sudo install -m 644 /tmp/assert-sync-users.service /tmp/assert-sync-users.timer /etc/systemd/system/
sudo install -d -m 755 /etc/assert-users /var/lib/assert-users
[ -d /var/lib/assert-users/repo ] || sudo git clone -q --depth 1 $REPO /var/lib/assert-users/repo
# escape hatch: admin key for root, never touched by the sync
sudo install -d -m 700 /root/.ssh
sudo touch /root/.ssh/authorized_keys
sudo grep -qF \"\$(cut -d' ' -f2 /tmp/martin.pub)\" /root/.ssh/authorized_keys || sudo sh -c 'cat /tmp/martin.pub >> /root/.ssh/authorized_keys'
sudo chmod 600 /root/.ssh/authorized_keys
rm /tmp/sync_users.py /tmp/assert-sync-users.service /tmp/assert-sync-users.timer /tmp/martin.pub
sudo systemctl daemon-reload
"
if [ "$ENABLE" = --enable ]; then
  ssh "$HOST" "sudo systemctl enable --now assert-sync-users.timer"
fi
