The same fixtures as `../lifecycle_20261127/`, rebuilt by its `make_fixtures.py` and `make_migration_fixtures.py` from COPIES of the production files taken at **18:29 UTC on 27 November 2026**: candles to 18:25, STP's own plans at every recorded analysis to 18:00 (123 plans, 0 differences from the journal), and the 10 STP-authorised trades.

They include the trade STP authorised at 15:11:16 (AB261127151117, `1500-59#t1`) before the owner's 16:26:57 restart switched authorisation off. On `fadf228` the replay to 18:30 reproduces production's journal for all 36 opportunities with no difference.
