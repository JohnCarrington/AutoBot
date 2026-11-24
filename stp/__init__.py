"""The STP strategy integration (owner, 24 November 2026; docs/design/STP_STRATEGY_INTEGRATION_20261124.md).

STP determines WHERE to trade (its live opportunities, planner/opportunities.py); the existing strategies determine
WHEN (their own confirmation, unchanged). Two parts here, both only while STP_AUTHORISES_ENTRIES is on:
  stp/levels.py     the live STP zones added to the STRATEGIES' copy of the level list (OD-22, OD-26)
  stp/authorise.py  the one authorisation check, called from trading/engine.py _place (OD-03, OD-25, OD-32)
stp/source.py reads STP's file; nothing here writes it.
"""
