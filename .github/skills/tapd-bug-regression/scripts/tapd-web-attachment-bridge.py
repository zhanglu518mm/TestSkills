#!/usr/bin/env python3
"""Upload TAPD bug attachments via web session and return preview links.

This bridge avoids OpenAPI upload limitations by reusing TAPD web login session.
It opens the bug detail page, uploads local files from the attachment panel,
and prints attachment_id + preview URL as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List


def _ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        print(
            "Playwright is required. Install with: pip install playwright ; playwright install",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return sync_playwright


def _expand_files(files: List[str]) -> List[Path]:
    out: List[Path] = []
    for raw in files:
        p = Path(raw).expanduser().resolve()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"file not found: {p}")
        out.append(p)
    return out


def _extract_attachment_id(url: str) -> str:
    m = re.search(r"/preview_attachments/(\d+)/", url)
    return m.group(1) if m else ""


def _expand_attachment_panel(page) -> None:
    page.evaluate(
        """
        () => {
          const heads = Array.from(document.querySelectorAll('h1,h2,h3,h4,div,span'))
            .filter(el => (el.textContent || '').trim() === '附件');
          for (const h of heads) {
            const wrap = h.closest('div');
            if (!wrap) continue;
            const btn = wrap.parentElement && wrap.parentElement.querySelector('button');
            if (btn) {
              btn.click();
              return true;
            }
          }
          return false;
        }
        """
    )


def _wait_for_login(page, tapd_web_base: str) -> None:
    if "cloud_logins/login" not in page.url:
        return
    print(
        "Please complete TAPD login in the opened browser, then press Enter...",
        file=sys.stderr,
    )
    input()
    page.wait_for_timeout(800)
    if "cloud_logins/login" in page.url:
        page.goto(tapd_web_base.rstrip("/") + "/my_dashboard", wait_until="domcontentloaded")


def _upload_one(page, file_path: Path) -> Dict[str, str]:
    _expand_attachment_panel(page)

    btn = page.get_by_role("button", name=re.compile(r"添加本地文件"))
    btn.first.wait_for(timeout=15000)

    with page.expect_file_chooser(timeout=15000) as fc:
        btn.first.click()
    chooser = fc.value
    chooser.set_files(str(file_path))

    name_locator = page.locator("a", has_text=file_path.name)
    name_locator.first.wait_for(timeout=20000)
    href = name_locator.first.get_attribute("href") or ""
    full_href = href if href.startswith("http") else "https://www.tapd.cn" + href
    return {
        "file_name": file_path.name,
        "attachment_id": _extract_attachment_id(full_href),
        "preview_url": full_href,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TAPD web attachment upload bridge")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--entity-id", required=True, help="Full TAPD entity id")
    parser.add_argument("--entity-type", default="bug", choices=["bug", "story", "task"])
    parser.add_argument("--file", action="append", required=True, help="Local file path, repeatable")
    parser.add_argument("--tapd-web-base", default=os.getenv("TAPD_WEB_BASE_URL", "https://www.tapd.cn"))
    parser.add_argument(
        "--storage-state",
        default=os.getenv("TAPD_WEB_STORAGE_STATE", ""),
        help="Optional Playwright storage state json path",
    )
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    args = parser.parse_args()

    files = _expand_files(args.file)
    target_url = (
        args.tapd_web_base.rstrip("/")
        + f"/tapd_fe/{args.workspace_id}/{args.entity_type}/detail/{args.entity_id}"
    )

    sync_playwright = _ensure_playwright()
    results: List[Dict[str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)

        context_kwargs = {}
        state_path = args.storage_state.strip()
        if state_path and Path(state_path).exists():
            context_kwargs["storage_state"] = state_path

        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        page.goto(target_url, wait_until="domcontentloaded")
        _wait_for_login(page, args.tapd_web_base)
        page.goto(target_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)

        for f in files:
            item = _upload_one(page, f)
            results.append(item)

        if state_path:
            Path(state_path).parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=state_path)

        browser.close()

    print(json.dumps({
        "workspace_id": args.workspace_id,
        "entity_id": args.entity_id,
        "entity_type": args.entity_type,
        "items": results,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
