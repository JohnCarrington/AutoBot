# Stage B: activation and rollback (STP authorises entries on IG DEMO)

Prepared 25 November 2026. **Not activated.** Stage B needs the owner's explicit approval. It brings production from
fc4db27 (Stage A) to the tip of stp-integration/wp8-review (the SHA in the hand-over; only the dashboard's Stage A/B
label, tests and these documents change: no trading, strategy or planner code) and changes one switch.

What Stage B does: the hourly Bollinger bounce, the Bollinger bounce 5m and the level reversal (stp_authorisation.strategies)
open only when their rejection candle reached a live STP opportunity in their direction (stp/authorise.py); for those
entries the analyser state, hourly context, RSI stretch, rule 3 (counter-trend tiring) and one view are not applied
(stp_authorisation.bypass_filters, OD-05, OD-30); rule 11's duplicate key gains the STP key (OD-32). Every other strategy,
rule, limit, stop and exit is unchanged.

## 1. Before activation (all must be OK)
    cd /opt/autobot
    .venv/bin/python -I docs/design/stp_strategy_integration_20261124/implementation/stage_b_preflight.py expect-off
It checks, read only: the code (HEAD, no uncommitted tracked changes); both services active; the effective switches as
the bot reads them (STP_OPPORTUNITIES and STP_BIDIRECTIONAL on, STP_AUTHORISES_ENTRIES off, ONE_SIGNAL_ONE_TRADE on,
TRADING on); IG account type DEMO and the demo address; IG DEMO connectivity from the price service's own log (logged
in, price stream connected, no error lines since its start); open trades held by the bot; order submissions sent
without an outcome; no unexpected IG position events; the STP file current and fresh, with its opportunity list.

Open trades: activation is safe with trades open (the restart takes them over, as every restart), but the owner may
prefer to activate with none open. Pending submissions must be 0.

## 2. Activate (the owner)
    cd /opt/autobot && git fetch origin && git status --short | grep -v '^??'     # must print nothing
    git merge --ff-only origin/stp-integration/wp8-review && git log --oneline -1  # the hand-over SHA
    cp -p /opt/autobot/.env /home/autobot/env-backups/env.$(date -u +%Y-%m-%d_%H%M%S)_pre-stage-b
    sed -i 's/^STP_AUTHORISES_ENTRIES=off$/STP_AUTHORISES_ENTRIES=on/' /opt/autobot/.env
    grep -n '^STP_' /opt/autobot/.env            # STP_OPPORTUNITIES=on, STP_BIDIRECTIONAL=on, STP_AUTHORISES_ENTRIES=on
    sudo systemctl restart autobot-prices.service
    sudo systemctl restart autobot-dashboard.service

## 3. After activation (all must be OK)
    .venv/bin/python -I docs/design/stp_strategy_integration_20261124/implementation/stage_b_preflight.py expect-on
    journalctl -u autobot-prices --since "-5 min" --no-pager | grep -E "Trading ON|taken over|Price stream connected"
The dashboard's STP tab and card now say "STAGE B — STP AUTHORISES ENTRIES: BOLLINGER BOUNCE, BOLLINGER BOUNCE 5M,
LEVEL REVERSAL" (blue) instead of "STAGE A — OBSERVE ONLY ..." (amber); Waiting and Watch & Wait opportunities show as
authorising. Each gated idea then leaves an "STP authorised" or "STP refused" line in data/records/GBPUSD/decisions.jsonl.

## 4. Rollback to Stage A (the owner; no code change needed: the newer code with the switch off is Stage A)
    cp -p /opt/autobot/.env /home/autobot/env-backups/env.$(date -u +%Y-%m-%d_%H%M%S)_stage-b
    sed -i 's/^STP_AUTHORISES_ENTRIES=on$/STP_AUTHORISES_ENTRIES=off/' /opt/autobot/.env
    sudo systemctl restart autobot-prices.service
    sudo systemctl restart autobot-dashboard.service
    .venv/bin/python -I docs/design/stp_strategy_integration_20261124/implementation/stage_b_preflight.py expect-off
Trades opened under Stage B keep their stops and take profits at IG and are managed as before after the restart.
Full rollback to before Stage A: /home/autobot/backups/stage-a-20261125/ROLLBACK.md.
