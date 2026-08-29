"""End-to-end smoke test: drive every page and assert nothing raises.

Streamlit renders exceptions into the DOM rather than failing the request, so
the check is for stException elements and for known content on each page.
"""
from __future__ import annotations

import sys
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8501"
SHOTS = "/tmp/shots"

PAGES = [
    ("", "How much is your data product worth?"),
    ("portfolio", "Data Product Portfolio"),
    ("product", "Estimated 3-year economic value"),
    ("value", "Value a Data Product"),
    ("compare", "Which product should we fund?"),
    ("advisor", "Value Advisor"),
    ("realisation", "Value Realisation"),
    ("reports", "Executive Business Case"),
    ("assumptions", "Assumption Register"),
    ("boardroom", "Data Product Value"),
    ("settings", "Settings"),
]


def settle(page, timeout=45_000):
    """Wait for Streamlit to finish its run."""
    page.wait_for_load_state("networkidle", timeout=timeout)
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        running = page.locator('[data-testid="stStatusWidget"]').count()
        if running == 0:
            break
        time.sleep(0.25)
    time.sleep(1.2)


def main() -> int:
    failures = []
    console_errors = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1512, "height": 1000})
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(f"pageerror: {e}"))

        for slug, expected in PAGES:
            page.goto(f"{BASE}/{slug}", wait_until="domcontentloaded")
            settle(page)

            exceptions = page.locator('[data-testid="stException"]')
            n = exceptions.count()
            if n:
                detail = exceptions.first.inner_text()[:900]
                failures.append(f"{slug}: {n} exception(s)\n{detail}")
            else:
                body = page.inner_text("body").lower()
                if expected.lower() not in body:
                    failures.append(f"{slug}: expected copy not found — {expected!r}")

            page.screenshot(path=f"{SHOTS}/{slug or 'home'}.png", full_page=False)
            print(f"  {slug or 'home':<14} {'FAIL' if n else 'ok'}")

        browser.close()

    real_errors = [e for e in console_errors
                   if "favicon" not in e.lower() and "manifest" not in e.lower()]
    if real_errors:
        print(f"\n{len(real_errors)} console error(s):")
        for e in real_errors[:8]:
            print("  -", e[:220])

    if failures:
        print(f"\n{len(failures)} PAGE FAILURE(S):\n")
        for f in failures:
            print(f, "\n")
        return 1
    print("\nPASS — every page rendered with no exceptions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
