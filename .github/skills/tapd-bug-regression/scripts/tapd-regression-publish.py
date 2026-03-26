#!/usr/bin/env python3
"""Publish TAPD regression comment with web-uploaded attachments.

Flow:
1) Upload attachments via web-session bridge script.
2) Build readable HTML comment with paragraph spacing.
3) Submit comment through TAPD OpenAPI /comments.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def _require_requests():
    try:
        import requests  # type: ignore
    except Exception as exc:
        print("requests is required. Install with: pip install requests", file=sys.stderr)
        raise SystemExit(2) from exc
    return requests


def _run_bridge(
    workspace_id: str,
    entity_id: str,
    entity_type: str,
    files: List[str],
    tapd_web_base: str,
    storage_state: str,
    headless: bool,
) -> Dict:
    bridge_path = Path(__file__).with_name("tapd-web-attachment-bridge.py")
    cmd = [
        sys.executable,
        str(bridge_path),
        "--workspace-id",
        workspace_id,
        "--entity-id",
        entity_id,
        "--entity-type",
        entity_type,
        "--tapd-web-base",
        tapd_web_base,
    ]
    if storage_state:
        cmd.extend(["--storage-state", storage_state])
    if headless:
        cmd.append("--headless")
    for f in files:
        cmd.extend(["--file", f])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.stderr.write(proc.stdout)
        raise SystemExit(proc.returncode)

    out = proc.stdout.strip()
    if not out:
        raise RuntimeError("bridge script returned empty output")

    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"invalid bridge json output: {out[:400]}") from exc


def _p(text: str) -> str:
    return f"<p>{text}</p>"


def _build_comment_html(
    env_url: str,
    check_results: List[str],
    image_titles: List[str],
    uploaded_items: List[Dict[str, str]],
    remark: str,
    regression_date: str,
) -> str:
    if len(image_titles) != len(uploaded_items):
        raise ValueError("image_titles count must match uploaded files count")

    chunks: List[str] = []
    chunks.append(_p("【回归结论】验证通过。"))
    chunks.append(_p(f"【回归时间】{regression_date}"))
    chunks.append(_p(f"【回归环境】{env_url}"))
    chunks.append("")

    chunks.append(_p("【验证结果】"))
    for idx, line in enumerate(check_results, start=1):
        chunks.append(_p(f"{idx}）{line}"))
    chunks.append("")

    chunks.append(_p("【截图证据】"))
    for idx, (title, item) in enumerate(zip(image_titles, uploaded_items), start=1):
        chunks.append(_p(f"实际验证通过截图{idx}：{title}"))
        chunks.append(_p(f"实际截图结果：{check_results[min(idx - 1, len(check_results) - 1)]}"))
        chunks.append(_p(f'<a href="{item["preview_url"]}" target="_blank">查看截图{idx}</a>'))
        chunks.append("")

    if remark.strip():
        chunks.append(_p(f"【备注】{remark.strip()}"))

    return "\n".join(chunks).strip() + "\n"


def _post_comment(
    workspace_id: str,
    entity_id: str,
    entity_type: str,
    html: str,
    api_base: str,
    token: str,
    user: str,
    password: str,
) -> Dict:
    requests = _require_requests()
    url = api_base.rstrip("/") + "/comments"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    auth = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif user and password:
        from requests.auth import HTTPBasicAuth  # type: ignore

        auth = HTTPBasicAuth(user, password)
    else:
        raise RuntimeError("missing auth: set TAPD_API_TOKEN or TAPD_API_USER/TAPD_API_PASSWORD")

    data = {
        "workspace_id": workspace_id,
        "entry_type": entity_type,
        "entry_id": entity_id,
        "description": html,
    }

    resp = requests.post(url, data=data, headers=headers, auth=auth, timeout=45)
    body_text = resp.text or ""

    parsed = None
    try:
        parsed = resp.json()
    except Exception:
        parsed = {"raw": body_text[:1000]}

    if resp.status_code >= 400:
        raise RuntimeError(f"comment post failed: HTTP {resp.status_code} {body_text[:300]}")

    return {
        "http_status": resp.status_code,
        "response": parsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload TAPD attachments and publish API HTML comment")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--entity-type", default="bug", choices=["bug", "story", "task"])
    parser.add_argument("--env-url", required=True)
    parser.add_argument("--check", action="append", required=True, help="Validation result line, repeatable")
    parser.add_argument("--file", action="append", required=True, help="Evidence file path, repeatable")
    parser.add_argument("--image-title", action="append", required=True, help="Image title, repeatable")
    parser.add_argument("--remark", default="")
    parser.add_argument("--regression-date", default=dt.date.today().isoformat())
    parser.add_argument("--save-html", default="", help="Optional path to save generated html")
    parser.add_argument("--dry-run", action="store_true", help="Only print payload, do not call comment API")
    parser.add_argument("--headless", action="store_true")

    parser.add_argument("--tapd-web-base", default=os.getenv("TAPD_WEB_BASE_URL", "https://www.tapd.cn"))
    parser.add_argument("--storage-state", default=os.getenv("TAPD_WEB_STORAGE_STATE", ""))
    parser.add_argument("--api-base", default=os.getenv("TAPD_API_BASE_URL", "https://api.tapd.cn"))

    args = parser.parse_args()

    if len(args.file) != len(args.image_title):
        raise SystemExit("--file count must equal --image-title count")

    bridge_result = _run_bridge(
        workspace_id=args.workspace_id,
        entity_id=args.entity_id,
        entity_type=args.entity_type,
        files=args.file,
        tapd_web_base=args.tapd_web_base,
        storage_state=args.storage_state,
        headless=args.headless,
    )

    uploaded_items = bridge_result.get("items", [])
    if not uploaded_items:
        raise SystemExit("no uploaded items returned from bridge")

    html = _build_comment_html(
        env_url=args.env_url,
        check_results=args.check,
        image_titles=args.image_title,
        uploaded_items=uploaded_items,
        remark=args.remark,
        regression_date=args.regression_date,
    )

    if args.save_html.strip():
        out_path = Path(args.save_html).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")

    result = {
        "workspace_id": args.workspace_id,
        "entity_id": args.entity_id,
        "entity_type": args.entity_type,
        "uploaded_items": uploaded_items,
        "comment_html": html,
    }

    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    token = os.getenv("TAPD_API_TOKEN", "")
    user = os.getenv("TAPD_API_USER", "")
    password = os.getenv("TAPD_API_PASSWORD", "")

    post_result = _post_comment(
        workspace_id=args.workspace_id,
        entity_id=args.entity_id,
        entity_type=args.entity_type,
        html=html,
        api_base=args.api_base,
        token=token,
        user=user,
        password=password,
    )
    result["comment_post"] = post_result
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
