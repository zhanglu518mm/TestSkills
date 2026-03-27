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
    """Wait for TAPD login without blocking on stdin (works in VS Code terminals)."""
    def _is_login_page(url: str) -> bool:
        return "cloud_logins/login" in url or "/login" in url

    if not _is_login_page(page.url):
        return

    print(
        "[TAPD] 登录页已弹出——请在浏览器中扫码登录（企业微信扫码），最多等待 120 秒…",
        file=sys.stderr,
    )
    try:
        page.wait_for_url(
            lambda url: not _is_login_page(url),
            timeout=120_000,
        )
    except Exception:
        pass  # timeout: proceed anyway, next goto will reveal if still logged out
    page.wait_for_timeout(800)


def _upload_one(page, file_path: Path, workspace_id: str, entity_id: str, entity_type: str) -> Dict[str, str]:
    """Upload via TAPD internal API (more reliable than UI button)."""
    import mimetypes
    mime = mimetypes.guess_type(str(file_path))[0] or "image/png"
    file_bytes = file_path.read_bytes()

    resp = page.request.fetch(
        "https://www.tapd.cn/api/entity/attachments/add_attachment_drag?needRepeatInterceptors=false",
        method="POST",
        multipart={
            "workspace_id": workspace_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "file": {"name": file_path.name, "mimeType": mime, "buffer": file_bytes},
        },
    )
    data = resp.json()
    print(f"  上传 {file_path.name} → HTTP {resp.status}", file=sys.stderr)

    # Fetch updated attachment list to get attachment_id
    list_resp = page.request.fetch(
        "https://www.tapd.cn/api/entity/attachments/attachment_list",
        method="GET",
        params={"workspace_id": workspace_id, "entity_id": entity_id, "entity_type": entity_type},
    )
    attachments = list_resp.json().get("data", {}).get("attachments", [])
    matched = next((a for a in attachments if a.get("filename") == file_path.name), None)
    att_id = matched["id"] if matched else ""
    preview_url = (
        f"https://www.tapd.cn/{workspace_id}/attachments/preview_attachments/{att_id}/{entity_type}?"
        if att_id else ""
    )
    return {
        "file_name": file_path.name,
        "attachment_id": att_id,
        "preview_url": preview_url,
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
            item = _upload_one(page, f, args.workspace_id, args.entity_id, args.entity_type)
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
