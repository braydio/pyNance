"""Automated UI/UX audit tool for Dashboard screenshots."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BREAKPOINTS = [500, 768, 1024, 1280]


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Capture Dashboard screenshots at common breakpoints"
    )
    parser.add_argument(
        "--url",
        default=os.getenv("DASHBOARD_URL", "http://localhost:5173"),
        help="Base URL of the running frontend",
    )
    parser.add_argument(
        "--output", default="uiux_audit", help="Directory to save screenshots"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait before taking a screenshot",
    )
    return parser.parse_args()


def run_audit(url: str, output: str, delay: float) -> None:
    """Open Dashboard at various widths and save screenshots."""
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width in BREAKPOINTS:
            context = browser.new_context(viewport={"width": width, "height": 900})
            page = context.new_page()
            page.goto(url)
            page.wait_for_timeout(delay * 1000)
            screenshot = out_dir / f"dashboard_{width}px.png"
            page.screenshot(path=str(screenshot))
            print(f"Saved screenshot: {screenshot}")
            context.close()
        browser.close()


def main() -> None:
    args = parse_args()
    run_audit(args.url, args.output, args.delay)


if __name__ == "__main__":
    main()
