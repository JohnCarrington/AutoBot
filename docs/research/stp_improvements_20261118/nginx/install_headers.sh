#!/bin/bash
# Installs the security-header correction for the dashboard's nginx site (proposed 18 November 2026). Run by the
# owner with sudo:   sudo bash install_headers.sh
# Backs up the live site, installs the corrected one (this folder's autobot-dashboard.nginx.proposed with this
# server's Tailscale address), validates with nginx -t, reloads only if valid, verifies the headers and the login
# through the real address, and restores the backup automatically if anything fails. Touches nothing else.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
SITE=/etc/nginx/sites-available/autobot-dashboard
BK=$SITE.bak-$(date -u +%Y%m%d%H%M%S)
TS=$(tailscale ip -4 | head -n1)
[ -n "$TS" ] || { echo "no Tailscale address"; exit 1; }
cp -a "$SITE" "$BK" || exit 1
echo "backup: $BK"
restore() { echo "ROLLBACK: $*"; cp -a "$BK" "$SITE" && nginx -t && systemctl reload nginx; echo "restored $BK"; exit 2; }
sed "s/TAILSCALE_IP/$TS/" "$HERE/autobot-dashboard.nginx.proposed" > "$SITE.new" && mv "$SITE.new" "$SITE" || restore "write failed"
nginx -t || restore "nginx -t failed"
systemctl reload nginx || restore "reload failed"
sleep 1
for p in / /api/status /favicon.svg; do
    n=$(curl -sI "http://$TS:3000$p" | grep -ciE '^(x-frame-options|content-security-policy|x-content-type-options|referrer-policy):')
    echo "$p: $n of 4 security headers"; [ "$n" = 4 ] || restore "$p lacks headers"
done
[ "$(curl -s -o /dev/null -w '%{http_code}' "http://$TS:3000/")" = 200 ] || restore "page not served"
[ "$(curl -s -o /dev/null -w '%{http_code}' "http://$TS:3000/api/status")" = 401 ] || restore "/api/status not gated"
[ "$(curl -s -o /dev/null -w '%{http_code}' "http://$TS:3000/api/stp/overview")" = 401 ] || restore "/api/stp not gated"
echo "OK: headers present, page served, API still needs the login. Backup kept at $BK."
