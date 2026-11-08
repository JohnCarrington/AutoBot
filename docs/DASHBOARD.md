# The dashboard

Built on 8 November 2026, hosted the same way as AutoBot 161's (nginx on port 3000, a password login page, a signed
session cookie), with one difference: **nginx listens only on this server's Tailscale address**, never on the public
address, and the dashboard's data service listens only on 127.0.0.1.

- **The page** (`dashboard/static/index.html`, served by nginx): the analyser's state and direction, the strategies
  allowed now (and any switched off), the open trades with live pips, today's trades and pips, warnings, whether
  `TRADING` is on, and the **pause new trades** switch (stops new trades; open trades are still managed). Each change
  of the switch is recorded (`data/records/<PAIR>/decisions.jsonl`) and sent on Telegram.
- **The data service** (`dashboard/server.py`, `deploy/autobot-dashboard.service`): 127.0.0.1:8766 only. Login:
  `DASHBOARD_PASSWORD`, compared in constant time; wrong passwords are limited (5 a minute in the service, 10 a
  minute in nginx). The session cookie is signed with `DASHBOARD_SECRET_KEY` (HMAC-SHA256), lasts 30 days, HttpOnly,
  SameSite=Strict. The pause switch also needs the session's csrf token and refuses another site's Origin. Without
  both secrets the service does not start (exit code 78; systemd does not restart it).
- **The status** comes from the price service (`data/trading/<PAIR>/status.json`, every 5 seconds); the dashboard
  warns when it is missing or more than 30 seconds old.
- **nginx** (`deploy/autobot-dashboard.nginx`): `listen <Tailscale address>:3000`; the page is public, `/api/` is
  gated by `auth_request` to the data service, `/auth` is rate limited; security headers (no framing, no other
  sites' scripts).

- **The look** (owner, 8 November 2026): AutoBot 161's colours (near-black, one green accent, red for losses, amber
  for warnings), fonts (Syne for headings, JetBrains Mono for the rest) and card style, simpler and showing only the
  new bot's information. The two fonts are kept on this server (`dashboard/static/fonts/`, SIL Open Font License,
  licences beside them) so the page loads nothing from elsewhere.

## Reloading after a change

- **The page** (`dashboard/static/`): nginx serves it straight from the repository, so a new version is live as soon
  as it is pulled; reload the browser page (on a phone, close and reopen the tab).
- **The nginx file** (`deploy/autobot-dashboard.nginx`): install it again and reload nginx:

      TSIP=$(tailscale ip -4 | head -n 1)
      sed "s/TAILSCALE_IP/$TSIP/" /opt/autobot/deploy/autobot-dashboard.nginx | sudo tee /etc/nginx/sites-available/autobot-dashboard > /dev/null
      sudo nginx -t && sudo systemctl reload nginx

- **The data service** (`dashboard/server.py`, `dashboard/auth.py`): `sudo systemctl restart autobot-dashboard`
  (logged-in sessions stay valid while `DASHBOARD_SECRET_KEY` is unchanged).

## Setting it up (needs sudo)

1. **Secrets** in `/opt/autobot/.env` (never shown or logged):

       DASHBOARD_PASSWORD=<a long password of your choice, at least 12 characters>
       DASHBOARD_SECRET_KEY=<64 random hex characters>

   Make the key with `python3 -c "import secrets; print(secrets.token_hex(32))"`. Keep the same key: changing it
   logs everyone out.

2. **Tailscale**, to join this server to your Tailscale network:

       curl -fsSL https://tailscale.com/install.sh | sh
       sudo tailscale up
       tailscale ip -4

   `sudo tailscale up` prints a link: open it and log in to your Tailscale account to add the server. The last
   command shows the server's Tailscale address (100.x.y.z).

3. **nginx**:

       sudo apt-get update && sudo apt-get install -y nginx
       sudo rm -f /etc/nginx/sites-enabled/default
       TSIP=$(tailscale ip -4 | head -n 1)
       sed "s/TAILSCALE_IP/$TSIP/" /opt/autobot/deploy/autobot-dashboard.nginx | sudo tee /etc/nginx/sites-available/autobot-dashboard > /dev/null
       sudo ln -sf /etc/nginx/sites-available/autobot-dashboard /etc/nginx/sites-enabled/autobot-dashboard
       echo 'net.ipv4.ip_nonlocal_bind = 1' | sudo tee /etc/sysctl.d/60-autobot-dashboard.conf && sudo sysctl --system
       sudo nginx -t && sudo systemctl restart nginx

   Removing nginx's default site stops it listening on port 80 on every address. The `ip_nonlocal_bind` line lets
   nginx start at boot even if Tailscale has not brought its address up yet.

4. **The data service**:

       sudo cp /opt/autobot/deploy/autobot-dashboard.service /etc/systemd/system/
       sudo systemctl daemon-reload && sudo systemctl enable --now autobot-dashboard

5. **Check**: `sudo ss -ltnp | grep -E ':3000|:8766'` must show port 3000 only on the 100.x.y.z address and 8766 only
   on 127.0.0.1. If the firewall (ufw) is on: `sudo ufw allow in on tailscale0 to any port 3000 proto tcp`.

Then, on a device logged in to the same Tailscale network, open `http://<100.x.y.z>:3000`.
