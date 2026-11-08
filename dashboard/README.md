# dashboard

**What it does:** The dashboard (design section 9; `docs/DASHBOARD.md`), hosted as AutoBot 161's but only on this server's Tailscale address: nginx on port 3000 serves the page (`static/index.html`) and asks the data service (`server.py`, 127.0.0.1:8766 only) whether each request's signed session cookie is genuine. It shows the analyser's state and direction, the strategies allowed now, the open trades with live pips, today's trades and pips, warnings, whether `TRADING` is on, and the "pause new trades" switch. Login: `DASHBOARD_PASSWORD` (constant-time, rate limited); cookie signed with `DASHBOARD_SECRET_KEY` (`auth.py`).

**What it must never do:** Never listen on the public address. Never place, change or close a trade (its one action is the pause switch, which only stops new trades). Never start without both secrets.
