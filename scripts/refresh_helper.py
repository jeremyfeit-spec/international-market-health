"""
Local refresh helper — listens on http://localhost:7325 for refresh
requests from the dashboard's "Refresh VOC" button.

Why a local helper: the dashboard is served from GitHub Pages, but
scrapers can't run from there. The button's click POSTs to localhost,
which (because the user is running this script) actually has network
access to Trustpilot/G2/Capterra/etc.

CORS allows GitHub Pages origin so the button works without browser
extensions. Keeps to localhost-only, no external exposure.

Run it:
    python3 scripts/refresh_helper.py

Then click "Refresh VOC" in the dashboard. The helper logs each request,
runs the scraper, rebuilds the digest, and (optionally) git-commits the
change. The button polls for status.

Stop it: Ctrl-C.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PORT = 7325
ALLOWED_ORIGINS = {
    "https://jeremyfeit-spec.github.io",
    "http://localhost:8000",  # local preview if you ever serve docs/ locally
    "http://127.0.0.1:8000",
}

# Single in-memory job-state (tiny, single-user)
state = {
    "current_job": None,        # one of: None, "running", "succeeded", "failed"
    "started_at": None,
    "ended_at": None,
    "stdout_tail": [],
    "error": None,
    "summary": None,
}
state_lock = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def run_pipeline() -> None:
    """Run scraper → build_voc → build_final_digest. Updates `state` as it goes."""
    with state_lock:
        state.update({
            "current_job": "running",
            "started_at": now_iso(),
            "ended_at": None,
            "stdout_tail": [],
            "error": None,
            "summary": None,
        })

    log_lines: list[str] = []

    def push(line: str) -> None:
        line = line.rstrip()
        if not line:
            return
        log_lines.append(line)
        with state_lock:
            state["stdout_tail"] = log_lines[-30:]

    try:
        # Three-step pipeline: scrape → rebuild VOC → rebuild final digest.
        # All three scripts live in scripts/ alongside this helper.
        steps = [
            ([sys.executable, str(REPO / "scripts" / "voc_scraper.py")],       "1/3 scraper"),
            ([sys.executable, str(REPO / "scripts" / "build_voc.py")],         "2/3 build_voc"),
            ([sys.executable, str(REPO / "scripts" / "build_final_digest.py")], "3/3 build_final_digest"),
        ]
        for cmd, label in steps:
            push(f"--- {label} ---")
            proc = subprocess.Popen(
                cmd, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            for line in proc.stdout:
                push(line)
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"{label} exited with {proc.returncode}")

        # Read scrape summary from cache file
        cache_file = REPO / "docs" / "data" / "voc_cache.json"
        summary = {}
        if cache_file.exists():
            try:
                cache = json.loads(cache_file.read_text())
                summary = cache.get("last_run_summary", {})
                summary["last_run_at"] = cache.get("last_run_at")
            except json.JSONDecodeError:
                pass

        with state_lock:
            state["current_job"] = "succeeded"
            state["ended_at"] = now_iso()
            state["summary"] = summary
        push(f"--- DONE · {summary.get('successes', '?')} OK, {summary.get('failures', '?')} failed ---")

    except Exception as e:
        with state_lock:
            state["current_job"] = "failed"
            state["ended_at"] = now_iso()
            state["error"] = str(e)
        push(f"--- ERROR · {e} ---")


def cors_origin(origin: str) -> str:
    return origin if origin in ALLOWED_ORIGINS else ""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass  # silence default logging — we have our own

    def _set_cors(self):
        origin = self.headers.get("Origin", "")
        allowed = cors_origin(origin)
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors()
            self.end_headers()
            with state_lock:
                self.wfile.write(json.dumps(state).encode())
            return
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors()
            self.end_headers()
            self.wfile.write(b'{"ok": true, "service": "intl-market-health-refresh"}')
            return
        self.send_response(404)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/refresh":
            self.send_response(404); self._set_cors(); self.end_headers(); return

        with state_lock:
            if state["current_job"] == "running":
                self.send_response(409)
                self.send_header("Content-Type", "application/json")
                self._set_cors()
                self.end_headers()
                self.wfile.write(b'{"error": "already_running"}')
                return

        threading.Thread(target=run_pipeline, daemon=True).start()
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self._set_cors()
        self.end_headers()
        self.wfile.write(b'{"started": true}')


def main():
    print(f"VOC refresh helper listening on http://localhost:{PORT}")
    print(f"Repo: {REPO}")
    print(f"Allowed origins: {sorted(ALLOWED_ORIGINS)}")
    print("Endpoints: GET /healthz · GET /status · POST /refresh")
    print("Press Ctrl-C to stop.\n")
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
