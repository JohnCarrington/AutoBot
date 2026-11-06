"""Log rotation by size and age, and the low disk space warning."""

import logging

from housekeeping.disk import check_free_space
from housekeeping.logs import SizeAndAgeRotatingHandler, UKTimeFormatter
from tests.technical.fake_stream import SETTINGS


class FakeTime:
    """Starts at the real time, because file ages are measured from the files' real timestamps."""

    def __init__(self):
        import time
        self.t = time.time()

    def __call__(self):
        return self.t


def _logger(handler):
    lg = logging.getLogger(f"test-rotation-{id(handler)}")
    lg.propagate = False
    lg.handlers[:] = [handler]
    lg.setLevel(logging.INFO)
    return lg


def test_log_limits_are_settings():
    hk = SETTINGS.housekeeping
    assert (hk.log_max_file_mb, hk.log_new_file_every_hours, hk.log_keep_files, hk.log_max_age_days) == (10, 24, 20, 30)
    assert hk.min_free_disk_mb == 2048


def test_logs_rotate_by_size_and_never_keep_more_than_the_limit(tmp_path):
    h = SizeAndAgeRotatingHandler(tmp_path / "bot.log", max_bytes=1000, new_file_every_seconds=86400,
                                  keep_files=3, max_age_seconds=30 * 86400, clock=FakeTime())
    lg = _logger(h)
    for i in range(500):
        lg.info("x" * 50)
    h.close()
    files = sorted(p.name for p in tmp_path.iterdir() if not p.name.endswith(".started"))
    assert files == ["bot.log", "bot.log.1", "bot.log.2", "bot.log.3"]
    assert all(p.stat().st_size <= 1100 for p in tmp_path.iterdir())


def test_logs_rotate_by_age(tmp_path):
    clock = FakeTime()
    h = SizeAndAgeRotatingHandler(tmp_path / "bot.log", max_bytes=10**9, new_file_every_seconds=3600,
                                  keep_files=5, max_age_seconds=30 * 86400, clock=clock)
    lg = _logger(h)
    lg.info("first")
    clock.t += 3599
    lg.info("same file")
    assert not (tmp_path / "bot.log.1").exists()
    clock.t += 2
    lg.info("new file")
    h.close()
    assert "first" in (tmp_path / "bot.log.1").read_text()
    assert (tmp_path / "bot.log").read_text().strip().endswith("new file")


def test_old_log_files_are_deleted(tmp_path):
    import os
    clock = FakeTime()
    for n in (1, 2):
        p = tmp_path / f"bot.log.{n}"
        p.write_text("old")
    os.utime(tmp_path / "bot.log.2", (clock.t - 31 * 86400, clock.t - 31 * 86400))
    os.utime(tmp_path / "bot.log.1", (clock.t - 1 * 86400, clock.t - 1 * 86400))
    h = SizeAndAgeRotatingHandler(tmp_path / "bot.log", max_bytes=10**9, new_file_every_seconds=3600,
                                  keep_files=5, max_age_seconds=30 * 86400, clock=clock)
    h.close()
    assert (tmp_path / "bot.log.1").exists() and not (tmp_path / "bot.log.2").exists()


def test_log_lines_show_uk_time():
    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "hello", None, None)
    rec.created = 1_783_328_400.0   # 2026-07-06 09:00 UTC
    assert UKTimeFormatter("%(asctime)s %(message)s").format(rec) == "2026-07-06 10:00:00 BST hello"


def test_low_disk_space_writes_a_warning(tmp_path):
    warnings = []
    free = check_free_space(tmp_path, 2048, warnings.append, measure=lambda p: 1000)
    assert free == 1000 and len(warnings) == 1 and "LOW DISK SPACE" in warnings[0]
    check_free_space(tmp_path, 2048, warnings.append, measure=lambda p: 5000)
    assert len(warnings) == 1
