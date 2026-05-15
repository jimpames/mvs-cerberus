"""
Cerberus Gate — middleware for tso3270.com
  • Serves the MVS CERBERUS auth banner at /auth
  • Validates credentials against Windows (LogonUser)
  • Spawns/kills proxy3270.exe on demand to gate the TN3270 path
  • Tracks active sessions with a configurable lease

Designed to run on the same Windows host that hosts the
Hyper-V TurnKey MVS guest, behind the ngrok HTTPS tunnel
that fronts tso3270.com.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import socket
import subprocess
import threading
import time
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, render_template, request, session, redirect, url_for, jsonify

# Windows auth — pywin32
try:
    import win32security
    import win32con
    import pywintypes
    WINDOWS_AUTH = True
except ImportError:
    WINDOWS_AUTH = False  # dev mode on non-Windows; auth always fails closed

# ──────────────────────────────────────────────────────────────────────────────
# Configuration — edit these to match your environment
# ──────────────────────────────────────────────────────────────────────────────

CONFIG = {
    # Hyper-V TurnKey MVS guest — where TSO actually listens
    "mvs_host": os.environ.get("CERBERUS_MVS_HOST", "192.168.137.10"),
    "mvs_port": int(os.environ.get("CERBERUS_MVS_PORT", "3270")),

    # proxy3270 binary + the local port it should listen on
    # (ngrok TCP tunnel forwards tso3270.com:3270 → 127.0.0.1:CERBERUS_PROXY_PORT)
    "proxy3270_bin": os.environ.get("CERBERUS_PROXY3270_BIN", r"C:\cerberus\proxy3270.exe"),
    "proxy3270_port": int(os.environ.get("CERBERUS_PROXY_PORT", "3270")),

    # Windows auth domain. "." = local accounts on this host. Set to AD domain
    # name (e.g. "CORP") to authenticate against a domain controller.
    "auth_domain": os.environ.get("CERBERUS_AUTH_DOMAIN", "."),

    # How long a successful auth keeps proxy3270 alive (minutes)
    "session_minutes": int(os.environ.get("CERBERUS_SESSION_MINUTES", "15")),

    # Where to write the dynamically-generated proxy3270 config
    "proxy3270_config": os.environ.get(
        "CERBERUS_PROXY3270_CONFIG", r"C:\cerberus\proxy3270.json"
    ),

    # Flask secret — generate once and stash in env
    "flask_secret": os.environ.get("CERBERUS_FLASK_SECRET", secrets.token_hex(32)),

    # Public hostname/port the user's 3270 emulator should connect to
    # (what the success page tells them)
    "public_hostname": os.environ.get("CERBERUS_PUBLIC_HOST", "tso3270.com"),
    "public_port": int(os.environ.get("CERBERUS_PUBLIC_PORT", "3270")),
}

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("cerberus")

# ──────────────────────────────────────────────────────────────────────────────
# Session manager — tracks who's authed and runs proxy3270 lifecycle
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Session:
    sid: str
    username: str
    granted_at: datetime
    expires_at: datetime
    client_ip: str

    def remaining_seconds(self) -> int:
        return max(0, int((self.expires_at - datetime.now(timezone.utc)).total_seconds()))

    def expired(self) -> bool:
        return self.remaining_seconds() == 0


class GateManager:
    """Single-instance proxy3270 lifecycle with reference-counted sessions."""

    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: dict[str, Session] = {}
        self._proc: subprocess.Popen | None = None
        self._reaper_thread = threading.Thread(
            target=self._reaper_loop, daemon=True, name="cerberus-reaper"
        )
        self._reaper_thread.start()

    # ── public API ────────────────────────────────────────────────────────────

    def grant(self, username: str, client_ip: str) -> Session:
        with self._lock:
            sid = secrets.token_urlsafe(16)
            now = datetime.now(timezone.utc)
            sess = Session(
                sid=sid,
                username=username,
                granted_at=now,
                expires_at=now + timedelta(minutes=CONFIG["session_minutes"]),
                client_ip=client_ip,
            )
            self._sessions[sid] = sess
            log.info(
                "Granted session %s for user=%s ip=%s expires=%s",
                sid[:8], username, client_ip, sess.expires_at.isoformat()
            )
            self._ensure_proxy_running()
            return sess

    def revoke(self, sid: str) -> bool:
        with self._lock:
            if sid in self._sessions:
                log.info("Revoking session %s", sid[:8])
                del self._sessions[sid]
                self._maybe_stop_proxy()
                return True
            return False

    def status(self) -> dict:
        with self._lock:
            active = [s for s in self._sessions.values() if not s.expired()]
            return {
                "active_sessions": len(active),
                "proxy_running": self._proc is not None and self._proc.poll() is None,
                "proxy_port": CONFIG["proxy3270_port"],
                "sessions": [
                    {
                        "user": s.username,
                        "ip": s.client_ip,
                        "remaining_sec": s.remaining_seconds(),
                    }
                    for s in active
                ],
            }

    # ── proxy3270 lifecycle ──────────────────────────────────────────────────

    def _ensure_proxy_running(self):
        """Start proxy3270 if not already running. Called with lock held."""
        if self._proc and self._proc.poll() is None:
            return  # already running

        # Write a fresh config pointing at the MVS guest
        config = {
            "ListenPort": CONFIG["proxy3270_port"],
            "Hosts": [
                {
                    "Name": "MVS Cerberus",
                    "Description": "TurnKey MVS TSO",
                    "Hostname": CONFIG["mvs_host"],
                    "Port": CONFIG["mvs_port"],
                }
            ],
        }
        cfg_path = Path(CONFIG["proxy3270_config"])
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(config, indent=2))

        bin_path = CONFIG["proxy3270_bin"]
        if not Path(bin_path).exists():
            log.error("proxy3270 binary not found at %s", bin_path)
            raise RuntimeError(f"proxy3270 binary not found at {bin_path}")

        log.info("Spawning proxy3270: %s -config %s", bin_path, cfg_path)
        self._proc = subprocess.Popen(
            [bin_path, "-config", str(cfg_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )

        # Quick sanity probe — wait up to 3s for the port to accept connections
        deadline = time.time() + 3
        while time.time() < deadline:
            with suppress(OSError):
                with socket.create_connection(
                    ("127.0.0.1", CONFIG["proxy3270_port"]), timeout=0.5
                ):
                    log.info("proxy3270 listening on :%d", CONFIG["proxy3270_port"])
                    return
            time.sleep(0.2)
        log.warning(
            "proxy3270 did not begin listening within 3s — check logs of pid=%d",
            self._proc.pid,
        )

    def _maybe_stop_proxy(self):
        """Stop proxy3270 if there are no active sessions. Called with lock held."""
        active = [s for s in self._sessions.values() if not s.expired()]
        if active:
            return
        if not self._proc:
            return
        log.info("No active sessions — terminating proxy3270 pid=%d", self._proc.pid)
        with suppress(Exception):
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    def _reaper_loop(self):
        """Periodically expire stale sessions and reap proxy3270 if idle."""
        while True:
            time.sleep(10)
            with self._lock:
                expired = [sid for sid, s in self._sessions.items() if s.expired()]
                for sid in expired:
                    log.info("Session %s expired", sid[:8])
                    del self._sessions[sid]
                if expired:
                    self._maybe_stop_proxy()


GATE = GateManager()

# ──────────────────────────────────────────────────────────────────────────────
# Windows authentication
# ──────────────────────────────────────────────────────────────────────────────

def authenticate_windows(username: str, password: str) -> bool:
    """Validate credentials against the local Windows account database
    (or AD if CERBERUS_AUTH_DOMAIN is set). Returns True on success."""
    if not WINDOWS_AUTH:
        log.warning("pywin32 not available — auth fails closed")
        return False

    domain = CONFIG["auth_domain"]
    try:
        token = win32security.LogonUser(
            username,
            domain,
            password,
            win32con.LOGON32_LOGON_NETWORK,
            win32con.LOGON32_PROVIDER_DEFAULT,
        )
        if token:
            token.Close()
            return True
        return False
    except pywintypes.error as e:
        # error 1326 = "logon failure: unknown user or bad password"
        log.info("LogonUser failed for %r: %s", username, e)
        return False
    except Exception as e:
        log.exception("Unexpected error in LogonUser: %s", e)
        return False

# ──────────────────────────────────────────────────────────────────────────────
# Flask app
# ──────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = CONFIG["flask_secret"]


def client_ip() -> str:
    """Get the real client IP, trusting X-Forwarded-For only if set by ngrok."""
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or "unknown"


@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("auth"))


@app.route("/auth", methods=["GET", "POST"])
def auth():
    error = None
    if request.method == "POST":
        username = (request.form.get("logon_id") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            error = "LOGON ID AND PASSWORD REQUIRED"
        elif authenticate_windows(username, password):
            sess = GATE.grant(username=username, client_ip=client_ip())
            session["sid"] = sess.sid
            session["user"] = sess.username
            return redirect(url_for("granted"))
        else:
            log.info("Auth failure user=%r ip=%s", username, client_ip())
            error = "ACCESS DENIED — INVALID CREDENTIALS"

    return render_template("cerberus.html", error=error)


@app.route("/granted")
def granted():
    sid = session.get("sid")
    if not sid:
        return redirect(url_for("auth"))
    state = GATE.status()
    my_sessions = [s for s in state["sessions"] if s.get("ip") == client_ip()]
    remaining = my_sessions[0]["remaining_sec"] if my_sessions else 0
    return render_template(
        "granted.html",
        user=session.get("user"),
        hostname=CONFIG["public_hostname"],
        port=CONFIG["public_port"],
        remaining=remaining,
    )


@app.route("/logout", methods=["POST"])
def logout():
    sid = session.pop("sid", None)
    session.pop("user", None)
    if sid:
        GATE.revoke(sid)
    return redirect(url_for("auth"))


@app.route("/status")
def status():
    # Could be lock-down to localhost if you want
    return jsonify(GATE.status())


# ──────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Cerberus Gate starting")
    log.info("MVS upstream: %s:%d", CONFIG["mvs_host"], CONFIG["mvs_port"])
    log.info("proxy3270 binary: %s", CONFIG["proxy3270_bin"])
    log.info("Public endpoint: %s:%d", CONFIG["public_hostname"], CONFIG["public_port"])
    log.info("Windows auth: %s (domain=%s)", "ENABLED" if WINDOWS_AUTH else "DISABLED",
             CONFIG["auth_domain"])
    # In production, put this behind a real WSGI server (waitress on Windows)
    app.run(host="127.0.0.1", port=5000, debug=False)
