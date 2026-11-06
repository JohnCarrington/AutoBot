# housekeeping

**What it does:** Keeps the server tidy so the bot can run for months: rotates log files by size and by age (with limits from the settings file, so logs can never fill the disk), and warns when free disk space falls below a set level.

**What it must never do:** Never delete candles or trade records. Only old rotated log files are ever deleted.
