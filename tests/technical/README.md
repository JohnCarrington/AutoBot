# tests/technical

Tests that check the code itself works: for example, that every setting loads with the right value and that a bad settings file stops the bot with a clear message.

Tests never read the real `.env` (which holds the IG secrets): `tests/conftest.py` points every test at a pretend switches file (GBPUSD only). `test_pairs.py` runs every part with two pretend pairs switched on, EURUSD and a JPY pair (EURJPY, set to 10 of IG's points a pip on purpose), so any mix-up between pairs fails a test.
