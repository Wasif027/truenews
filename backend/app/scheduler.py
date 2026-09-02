"""Optional in-process ingestion loop.

Enabled by INGEST_INTERVAL_MIN > 0. Runs the full pipeline on a background
daemon thread every N minutes. For local dev this makes new stories (and the
"new stories" pill in the UI) appear on their own. For the deployed version,
prefer the GitHub Actions cron and leave this at 0 so ingestion doesn't run
twice against the same database.
"""

from __future__ import annotations

import logging
import threading
import time

from app.config import get_settings

log = logging.getLogger("truenews.scheduler")


def start_scheduler() -> None:
    interval = get_settings().ingest_interval_min
    if interval <= 0:
        return

    def loop() -> None:
        from app.ingest.pipeline import run_all

        time.sleep(15)  # let the API finish starting before the first run
        while True:
            try:
                log.info("scheduled ingest: %s", run_all())
            except Exception:
                log.exception("scheduled ingest failed; will retry next cycle")
            time.sleep(interval * 60)

    threading.Thread(target=loop, name="truenews-ingest", daemon=True).start()
    log.info("in-process ingest scheduler started: every %d min", interval)
