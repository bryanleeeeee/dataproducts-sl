"""Interaction test: exercise the parts a smoke test cannot reach —
theme switching, the Explain and Advisor dialogs, what-if levers, the
detailed wizard and navigation between pages.
"""
from __future__ import annotations

import sys
import time

from playwright.sync_api import sync_playwright, expect

BASE = "http://127.0.0.1:8501"
SHOTS = "/tmp/shots"


def settle(page, timeout=45_000):
    page.wait_for_load_state("networkidle", timeout=timeout)
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        if page.locator('[data-testid="stStatusWidget"]').count() == 0:
            break
        time.sleep(0.25)
    time.sleep(1.0)


def no_exception(page, label, failures):
    n = page.locator('[data-testid="stException"]').count()
    if n:
        failures.append(f"{label}: {page.locator('[data-testid=stException]').first.inner_text()[:600]}")
        return False
    return True


def main() -> int:
    failures = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1512, "height": 1000})

        # 1 — dark theme
        page.goto(BASE, wait_until="domcontentloaded")
        settle(page)
        page.get_by_role("button", name="☾  Switch to dark").click()
        settle(page)
        bg = page.evaluate("getComputedStyle(document.querySelector('.stApp')).backgroundColor")
        if bg.replace(" ", "") not in ("rgb(13,18,28)",):
            failures.append(f"dark theme: .stApp background is {bg}, expected the dark surface token")
        page.screenshot(path=f"{SHOTS}/dark-dashboard.png")
        no_exception(page, "dark dashboard", failures)

        # 2 — the theme survives a hard reload via the query string, and carries
        #     to a chart-heavy page reached through in-app navigation
        page.reload(wait_until="domcontentloaded")
        settle(page)
        bg = page.evaluate("getComputedStyle(document.querySelector('.stApp')).backgroundColor")
        if bg.replace(" ", "") != "rgb(13,18,28)":
            failures.append(f"persistence: theme lost on reload (background {bg})")
        page.get_by_role("link", name="Portfolio").click()
        settle(page)
        page.get_by_role("button", name="Open valuation →").click()
        settle(page)
        if "estimated 3-year economic value" not in page.inner_text("body").lower():
            failures.append("nav: opening a valuation from the portfolio did not land on it")
        settle(page)
        page.screenshot(path=f"{SHOTS}/dark-product.png")
        no_exception(page, "dark product", failures)

        # 3 — Explain dialog
        explain = page.get_by_role("button", name="Explain ·").first
        if explain.count() == 0:
            failures.append("explain: no Explain button found on the valuation")
        else:
            explain.click()
            settle(page)
            dialog = page.locator('[role="dialog"]')
            if dialog.count() == 0:
                failures.append("explain: dialog did not open")
            else:
                # Several labels are uppercased by CSS, so compare case-insensitively.
                text = dialog.inner_text().lower()
                for want in ("formula", "source inputs", "annual value", "evidence"):
                    if want not in text:
                        failures.append(f"explain dialog: missing {want!r}")
                page.screenshot(path=f"{SHOTS}/dark-explain.png")
            no_exception(page, "explain dialog", failures)
            page.keyboard.press("Escape")
            settle(page)

        # 4 — what-if lever recomputes
        page.get_by_role("button", name="☀  Switch to light").click()
        settle(page)
        before = page.inner_text("body")
        slider = page.locator('[data-testid="stSlider"]').first
        slider.scroll_into_view_if_needed()
        box = slider.bounding_box()
        page.mouse.click(box["x"] + box["width"] * 0.2, box["y"] + box["height"] / 2)
        settle(page)
        if page.inner_text("body") == before:
            failures.append("what-if: moving a lever did not change the page")
        no_exception(page, "what-if", failures)

        # 5 — the Advisor answers a question about the open product
        page.get_by_role("link", name="Value Advisor").click()
        settle(page)
        page.get_by_role("button", name="Are my assumptions reasonable?").click()
        settle(page)
        body = page.inner_text("body").lower()
        if "guardrail" not in body and "challenge" not in body:
            failures.append("advisor: answer did not mention guardrails or challenges")
        page.screenshot(path=f"{SHOTS}/advisor.png")
        no_exception(page, "advisor", failures)

        # 6 — detailed wizard opens and steps forward
        page.goto(f"{BASE}/value", wait_until="domcontentloaded")
        settle(page)
        page.get_by_role("tab", name="Detailed").click()
        settle(page)
        if "What are you building?" not in page.inner_text("body"):
            failures.append("wizard: step 1 did not render")
        # Streamlit commits a text input on blur/Enter, not on keystroke.
        page.get_by_label("Product name *").fill("Test Product")
        page.get_by_label("Product name *").press("Enter")
        settle(page)
        page.get_by_label("Product owner *").fill("Test Owner")
        page.get_by_label("Product owner *").press("Enter")
        settle(page)
        page.get_by_role("button", name="Continue →").click()
        settle(page)
        if "Who benefits?" not in page.inner_text("body"):
            failures.append("wizard: did not advance to step 2")
        page.screenshot(path=f"{SHOTS}/wizard.png")
        no_exception(page, "wizard", failures)

        # 7 — sidebar navigation
        page.get_by_role("link", name="Reports").click()
        settle(page)
        if "Executive Business Case" not in page.inner_text("body"):
            failures.append("nav: Reports link did not navigate")
        no_exception(page, "nav", failures)

        browser.close()

    if failures:
        print(f"{len(failures)} INTERACTION FAILURE(S):\n")
        for f in failures:
            print(" -", f, "\n")
        return 1
    print("PASS — theme switch, dialogs, levers, wizard and navigation all work.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
