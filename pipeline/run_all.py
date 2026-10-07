
import json
import logging
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import duckdb

DB_PATH = "quickbite.duckdb"
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("logs/pipeline.log"), logging.StreamHandler()],
)
log = logging.getLogger("quickbite")


def send_alert(message):
    """The one alert: always written to logs/alerts.log, and sent to Slack if a webhook is set."""
    log.error("ALERT: %s", message)
    with open("logs/alerts.log", "a") as f:
        f.write(f"{datetime.now().isoformat()} ALERT: {message}\n")
    url = os.getenv("ALERT_WEBHOOK_URL")
    if url:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps({"text": f"QuickBite pipeline ALERT: {message}"}).encode(),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            log.error("Could not send webhook alert: %s", e)


def run_step(name, script):
    log.info("START %s", name)
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    if result.stdout.strip():
        log.info(result.stdout.strip())
    if result.returncode != 0:
        log.error(result.stderr.strip())
        send_alert(f"Step failed: {name}")
        sys.exit(1)
    log.info("DONE %s", name)


def main():
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not any(raw_dir.glob("*.*")):
        run_step("generate data", "generator/generate_data.py")
    else:
        log.info("Raw data found, skipping generator")

    run_step("load raw", "pipeline/load_raw.py")
    run_step("clean staging", "pipeline/clean_staging.py")
    run_step("build marts", "pipeline/build_marts.py")

    con = duckdb.connect(DB_PATH)
    try:
        bad = con.execute("SELECT COUNT(*) FROM staging.orders_quarantine").fetchone()[0]
        total = con.execute("SELECT COUNT(*) FROM raw.orders").fetchone()[0]
        log.info("Quarantined %s of %s raw orders (%.2f%%) - pipeline did not crash",
                 bad, total, 100 * bad / total)
        if os.getenv("DEMO_BREAK") == "1":
            log.warning("DEMO_BREAK=1: inserting a duplicate order on purpose")
            con.execute("INSERT INTO mart.orders_fact SELECT * FROM mart.orders_fact LIMIT 1")
    finally:
        con.close()

    log.info("START tests")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_pipeline.py", "-q"],
        capture_output=True, text=True,
    )
    log.info(result.stdout.strip())
    if result.returncode != 0:
        send_alert("Pipeline tests FAILED - see logs/pipeline.log")
        sys.exit(1)
    log.info("All tests passed. Pipeline complete.")


if __name__ == "__main__":
    main()
