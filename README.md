# Cerberus Gate

Middleware for `tso3270.com` that fronts a Hyper-V TurnKey MVS guest with
a web-auth banner page and on-demand `proxy3270` lifecycle management.

<img width="2730" height="1536" alt="mvs-cerberus" src="https://github.com/user-attachments/assets/ccf50aca-e9ae-477f-8559-78b43b92e821" />



## Architecture

```
  Browser ─── HTTPS ───┐                          ┌── ngrok TCP ── 3270 emulator
                       │                          │
   tso3270.com:443     │                          │   tso3270.com:3270
                       ▼                          ▼
                 ┌──────────────────────────────────────────┐
                 │  Windows Host                            │
                 │                                          │
                 │   Flask :5000  ──spawns──▶  proxy3270    │
                 │   (cerberus_gate.py)        :3270        │
                 │                                │         │
                 └────────────────────────────────┼─────────┘
                                                  ▼
                                     Hyper-V: TurnKey MVS
                                     TSO/3270 listener
```

## Setup

### 1. Install dependencies on the Windows host

```powershell
cd C:\cerberus
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Drop the proxy3270 binary

Build or download `proxy3270.exe` from
<https://github.com/racingmars/proxy3270> and place it at `C:\cerberus\proxy3270.exe`
(or override with `CERBERUS_PROXY3270_BIN`).

### 3. Set environment variables

```powershell
# Required — point at your MVS guest's IP on the Hyper-V virtual switch
$env:CERBERUS_MVS_HOST = "192.168.137.10"
$env:CERBERUS_MVS_PORT = "3270"

# Local accounts — leave as "." ;  AD — set to domain name
$env:CERBERUS_AUTH_DOMAIN = "."

# Public-facing info shown on the granted page
$env:CERBERUS_PUBLIC_HOST = "tso3270.com"
$env:CERBERUS_PUBLIC_PORT = "3270"

# Session lease length in minutes
$env:CERBERUS_SESSION_MINUTES = "15"

# Persist a Flask secret across restarts (rotate periodically)
$env:CERBERUS_FLASK_SECRET = "<paste-output-of: python -c 'import secrets;print(secrets.token_hex(32))'>"
```

### 4. ngrok configuration

You need two tunnels — one HTTPS (web auth), one TCP (3270 traffic).
Both pointed at `tso3270.com`. Edit `%USERPROFILE%\.ngrok2\ngrok.yml` or
`%APPDATA%\ngrok\ngrok.yml`:

```yaml
version: "3"
agent:
  authtoken: <your-ngrok-authtoken>
tunnels:
  cerberus-web:
    proto: http
    addr: 5000
    domain: tso3270.com         # requires a paid ngrok plan with custom domain
  cerberus-tcp:
    proto: tcp
    addr: 3270
    remote_addr: 1.tcp.ngrok.io:NNNNN   # or use a reserved TCP addr
```

Then `ngrok start --all`.

> **Note on the TCP endpoint hostname.** ngrok TCP tunnels normally use
> their own hostnames (e.g. `1.tcp.ngrok.io:12345`). To use `tso3270.com:3270`
> directly you need either a CNAME pointing to ngrok's reserved-TCP endpoint
> *plus* matching certificate (works only if you don't actually terminate
> TLS on it — pure TCP is fine), or a paid plan that supports a custom TCP
> domain. Easiest path: keep the web tunnel on `tso3270.com` and accept
> that the 3270 endpoint will be `1.tcp.ngrok.io:NNNNN` shown on the
> granted page.

### 5. Run

```powershell
# Dev / interactive
python cerberus_gate.py

# Production — waitress (Windows-friendly WSGI)
waitress-serve --host=127.0.0.1 --port=5000 cerberus_gate:app
```

For a real deployment, install as a Windows service with NSSM:
```
nssm install CerberusGate "C:\cerberus\venv\Scripts\waitress-serve.exe" ^
  --host=127.0.0.1 --port=5000 cerberus_gate:app
nssm set CerberusGate AppDirectory C:\cerberus
nssm start CerberusGate
```

## Operational notes

- **Auth backend.** `LogonUser` with `LOGON32_LOGON_NETWORK` validates against
  the local SAM (when `CERBERUS_AUTH_DOMAIN="."`) or an AD DC. The account
  used to authenticate doesn't need to be the same as the TSO/RACF user on
  MVS — this is a separate access gate. TSO will still demand its own
  credentials after the TN3270 connection lands.

- **Defense in depth.** The Cerberus Gate is the *outer* perimeter. The
  inner perimeter is TSO/RACF logon on MVS itself. Don't conflate them —
  use different credentials by design so a compromise of one doesn't
  hand over the other.

- **Multi-user.** Current design uses a single proxy3270 instance shared
  by all active sessions. If two people auth concurrently, both can use
  the TN3270 endpoint until the last one's lease expires. For per-user
  ports or stricter isolation, see the "v2 hardening" notes below.

- **Logging.** Auth attempts (success and failure) are logged to stderr.
  Pipe to Windows Event Log via NSSM's `AppStdout`/`AppStderr` settings.

- **The /status endpoint** returns JSON with current session counts and
  proxy state — handy for monitoring. Lock it down to localhost in
  production if you're paranoid.

## v2 hardening ideas (not yet implemented)

1. **In-band token at the 3270 layer.** Replace shared proxy3270 with a
   small go3270-based server that re-renders the CERBERUS banner inside
   the TN3270 session and asks for a session token issued by Flask. This
   closes the timing window where proxy3270 is open to anyone scanning
   the port.

2. **PROXY protocol v2 + IP allowlist.** Enable ngrok PROXY v2 on the
   TCP tunnel, parse the header in a Python TCP forwarder, and gate
   based on the real client IP captured at web-auth time.

3. **MFA.** TOTP via `pyotp` — add a third form field. Stage the secret
   in env or a sqlite store.

4. **Audit trail.** Persist auth events to a SQLite or ITGlue-friendly
   format. Tie session IDs to TN3270 connection logs from proxy3270.
