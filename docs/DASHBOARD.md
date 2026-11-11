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
- **Trading history** (owner, 9 November 2026): AutoBot 161's date picker, its layout, style and behaviour copied exactly: the Day / Week / Month / All period buttons; the date bar with its label, the date button that opens 161's month-grid calendar on a computer (Monday first, today outlined, later days greyed out, ‹ › for months, Today and Close; Escape or a click outside closes it) and the phone's own date picker on a touch screen; a month box for Month; "● Live" for the current period, or a Today button and "Historical view" for an earlier one. The one difference: it reads the bot's own trade records (`data/records/<PAIR>/trades.jsonl`, through the data service's `GET /api/history`), not IG, so it goes back to the very first trade with no 30-day limit. For the chosen day or period: the totals (pips, £, trades, wins and losses), a breakdown by strategy, and the trades in the same rows as the open trades (newest first). Real trades only by default; the **Show paper trades** switch adds the paper trades (`paper/trades.jsonl`), each marked paper. A trade the owner closed by hand at IG (owner, 11 November 2026) is listed, marked "closed by you · not counted", but never counted in the totals or the breakdown by strategy; the subtitle under the trades gives their number and pips. Today is the default view, and it refreshes every 5 seconds while it shows the current period. A trade counts on the UK day it closed (as the Today card and the daily summary); a week is Monday to Sunday and a month a calendar month, both in UK days.
- **The status** comes from the price service (`data/trading/<PAIR>/status.json`, every 5 seconds); the dashboard
  warns when it is missing or more than 30 seconds old.
- **nginx** (`deploy/autobot-dashboard.nginx`): `listen <Tailscale address>:3000`; the page is public, `/api/` is
  gated by `auth_request` to the data service, `/auth` is rate limited; security headers (no framing, no other
  sites' scripts).

- **The look** (owner, 8 November 2026): AutoBot 161's colours (near-black, one green accent, red for losses, amber
  for warnings), fonts (Syne for headings, JetBrains Mono for the rest) and card style, simpler and showing only the
  new bot's information. The two fonts are kept on this server (`dashboard/static/fonts/`, SIL Open Font License,
  licences beside them) so the page loads nothing from elsewhere.

- **Icons** (owner, 8 November 2026): AutoBot 161's `favicon.svg` (the browser tab), `icon-192.png` and `icon-512.png`
  with `manifest.json` (named "AutoBot") for adding the page to a phone's home screen, and `apple-touch-icon.png`
  (180 by 180, made from `icon-512.png`) for an iPhone's home screen. Served without the login, as 161 does.

## Reloading after a change

- **The page** (`dashboard/static/`): nginx serves it straight from the repository, so a new version is live as soon
  as it is pulled; reload the browser page (on a phone, close and reopen the tab).
- **The nginx file** (`deploy/autobot-dashboard.nginx`): install it again and reload nginx:

      TSIP=$(tailscale ip -4 | head -n 1)
      sed "s/TAILSCALE_IP/$TSIP/" /opt/autobot/deploy/autobot-dashboard.nginx | sudo tee /etc/nginx/sites-available/autobot-dashboard > /dev/null
      sudo nginx -t && sudo systemctl reload nginx

- **The data service** (`dashboard/server.py`, `dashboard/auth.py`; for example a new `/api/` address such as
  `/api/history`): `sudo systemctl restart autobot-dashboard`
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
