# Dashboard nginx — missing security headers (prepared, NOT applied)

**Status: not applied.** The autobot account has no sudo (`sudo -n true`: "a password is required"), so nginx cannot
be reloaded or its site file written. As the brief requires, nginx was left unchanged and the exact change is
prepared, validated and tested here for the owner to install with one command.

## Finding (live, 18 November 2026)

The site (`/etc/nginx/sites-available/autobot-dashboard`, identical to `deploy/autobot-dashboard.nginx` with the
Tailscale address) sets X-Frame-Options, X-Content-Type-Options, Referrer-Policy and Content-Security-Policy at server
level. nginx inherits server-level `add_header` only into a location with **no** `add_header` of its own; every
location here sets one (Cache-Control), so the live responses carry **none** of the four:
`/` 0 of 4, `/api/status` 0 of 4, `/favicon.svg` 0 of 4, `/fonts/` only nosniff.

Note: the dashboard endpoint is plain HTTP on the Tailscale address (`http://<tailscale-ip>:3000`, WireGuard-encrypted
inside Tailscale, by design since 8 November 2026); there is no HTTPS endpoint to verify.

## Change

`nginx/autobot-dashboard.nginx.proposed` (diff: `nginx/headers.diff`): each location that has its own `add_header`
repeats the four headers with exactly the server-level values. Authentication (`auth_request`), proxying, rate
limit, routes and the CSP itself are unchanged; nothing is weakened.

## Validation done without privileges

- `nginx -t` on the proposed site in a private wrapper config: syntax ok, test successful.
- The proposed site run as an unprivileged nginx on 127.0.0.1:18790 in front of the development harness: 4 of 4
  headers on `/`, `/api/status` (401), `/api/stp/overview` (401), `/favicon.svg`, an unknown path (404); login and
  the auth gate work through it.
- The full browser check (`chart_check.py`, 34 checks, desktop and phone) through that nginx with the CSP enforced:
  all passed, no CSP violation or script error. The CSP does not break the dashboard or the chart library.

## To install (owner)

    sudo bash /opt/autobot/docs/research/stp_improvements_20261118/nginx/install_headers.sh

It backs up the live site (`…autobot-dashboard.bak-<time>`), installs the proposed file with this server's Tailscale
address, runs `nginx -t`, reloads only if valid, verifies the four headers on `/`, `/api/status`, `/favicon.svg`, the
page (200) and the auth gate (401 on `/api/status` and `/api/stp/overview`) through the real address, and restores the
backup automatically on any failure. Afterwards the repository template `deploy/autobot-dashboard.nginx` should be
replaced by the proposed file (kept separate until it is actually installed, so the repository does not claim a
configuration that is not live).
