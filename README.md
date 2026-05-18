<img width="2730" height="1536" alt="mvs-cerberus (2)" src="https://github.com/user-attachments/assets/faf64fc1-0cb9-4737-bda6-b6c2471889f1" />
# MVS Cerberus

Source code: request DASD image via my email 
- this is based on zlinux , modified w python, go and ngrok support

### 3270 RADIUS Turret Firewall &mdash; ephemeral access, audited sessions, zero firewall configuration

> *Most network security products try to keep attackers out.*
> *Cerberus makes the door not exist until the right person knocks.*
> *Hack the net all you want &mdash; the tunnel to the admin of the machine is Cerberus only, and down till authed.*

---

<img width="1297" height="1013" alt="access-granted" src="https://github.com/user-attachments/assets/3a568c87-b368-4ae9-8007-52ed68c329a3" />


## What it does

Cerberus is an authenticated edge gateway for **3270 terminal access** to mainframe systems &mdash; TSO, VM/370, AS/400, SYSTEM/36, anything that speaks the 3270 datastream. It sits between users and your mainframes. It opens an ephemeral TN3270 path **only after** a user successfully authenticates. It closes that path the moment the session lease expires. It produces a complete audit record of every connection it ever brokered.

There is no permanent TN3270 port listening on the public internet. There is no port-forward to configure. There is no firewall rule to write. **The endpoint does not exist** until Cerberus summons it for an authorized user, and it ceases to exist when their lease ends.

A port scan against your reserved endpoint finds nothing. Reconnaissance finds nothing. The mainframe behind Cerberus is invisible to the network until auth grants visibility, for the duration of a lease, audited end to end.

This is **just-in-time access** taken to its logical conclusion.

---

## How it works

```
        Authorized User
              │
              ▼
   ┌──────────────────────────┐
   │   Cerberus Auth Page     │   persistent HTTPS endpoint
   │                          │
   └─────────────┬────────────┘
                 │  RADIUS · LDAP · SAML · OIDC · PassTicket
                 ▼
   ┌──────────────────────────┐
   │   Cerberus Gate          │   policy · grants · audit
   └─────────────┬────────────┘
                 │  grant event
                 ▼
   ┌──────────────────────────┐
   │   Ephemeral TCP Tunnel   │   exists only while leased
   └─────────────┬────────────┘
                 │
                 ▼
   ┌──────────────────────────┐
   │   Your Mainframes        │   TK5 · VM/370 · z/OS · S/36 · AS/400
   └──────────────────────────┘
```

1. User browses to `https://auth.your-domain/` and authenticates.
2. Gate validates against your identity source. If approved, it grants a session.
3. Exposure layer opens a TCP tunnel from a reserved endpoint to the local turret.
4. User points their TN3270 client at the granted endpoint.
5. Turret presents a backend menu, splices the user's session to the chosen mainframe.
6. Lease ticks down. Idle warning. Auto-revoke on expiry. Tunnel closes.
7. Audit log records every step.

---

## Distribution

**For Hercules / Hyperion**: free, open source, this repository. Drop the kit on any zLinux (or any Linux) host, run `./install.sh`, configure secrets, point it at your backends, run. Suitable for hobby mainframes, labs, training environments, and as a reference implementation.

**For real iron**: a commercial license includes a pre-built **DASD volume** containing a hardened zLinux 18.04 for System/390 with Cerberus, ngrok, Python, and Go pre-installed and pre-configured. Attach the DASD to your IFL engine. IPL it. Configure your identity source. You have a working 3270 access control plane &mdash; in your own LPAR, on hardware you already own, with zero new operational discipline to learn. Update process is "swap the DASD volume." [Contact for licensing](#commercial-licensing).

---

## Use cases

- **Banks**, **insurers**, **airlines**, **government**: gate operator and sysprog 3270 access with corporate identity (AD/Okta/Ping) and SIEM-grade audit logging, without changing how mainframe applications authenticate users
- **MSPs**: provide multi-tenant 3270 access to multiple customer mainframes through one gateway with per-customer audit and lease policies
- **Compliance teams**: produce technical evidence aligned to PCI-DSS, SOX, FFIEC, GDPR, FedRAMP, and NIST 800-53 access-control families
- **Hobbyist operators**: stop exposing your TK4-/TK5/VM/370 to the open internet, gate it behind real auth, keep a real audit trail
- **Lab and training environments**: give students time-limited, audited access to instructional mainframes without granting permanent network paths

---

## Quick start (Hercules / lab)

```bash
unzip mvs-cerberus-kit.zip -d ~/mvs-cerberus
cd ~/mvs-cerberus
sudo ./install.sh

# Edit secrets
sudo nano /etc/cerberus/environment

# Register your backends
sudo nano /etc/cerberus/cerberus.ini

# Bring it up
sudo systemctl start cerberus cerberus-https-tunnel

# Browse to your reserved domain and authenticate.
```

Full installation walkthrough: [`docs/deployment.md`](docs/deployment.md).
Architecture deep-dive: [`docs/architecture.md`](docs/architecture.md).
Security model and threat coverage: [`docs/security-model.md`](docs/security-model.md).

---

## Demo video

[**Watch the 18-minute end-to-end walkthrough**](https://youtu.be/H2Qwzw2yVME?si=vjHQphOvKwzaBKct)

Includes: install, configuration, first auth, granted endpoint, TN3270 client connecting through the tunnel to a TK5 backend, lease expiry, audit log.

---

## What's in the repo

| Path | What |
|---|---|
| `cerberus/` | Python package &mdash; gate, exposure, RADIUS, auth, turret, web |
| `cmd/cerberus-tunnel/` | Go binary &mdash; ngrok-backed ephemeral TCP tunnel manager |
| `etc/cerberus/` | Configuration templates (`cerberus.ini`, `environment`, `ngrok.yml`) |
| `etc/systemd/system/` | Systemd units for service management |
| `scripts/` | Operational scripts (`bringupall.sh`, `cerberus-tunnels.sh`, `freeze-dasd.sh`) |
| `static/` | Auth-page assets (CSS, the amber-CRT background artwork) |
| `docs/` | Architecture, deployment, configuration, security model, troubleshooting |
| `install.sh` | One-shot installer for any Linux host |

---

## Version notes

Current release in this repo: **v1 source**.

**v2 source** lands here on **18 May 2026** with:
- Refined gate policy engine
- Multi-backend menu in the turret
- SAML 2.0 and OIDC auth backends
- HA pair support
- SIEM integration helpers (Splunk, QRadar, generic CEF)
- The updated amber-CRT auth-page artwork

If you cloned v1 in the last 12 hours, thanks for showing up early. Watch this space.

---

## Why this exists

Existing tools for 3270 access control fall into three groups:

- **Mainframe-side identity products** (RACF/ACF2/Top Secret, PassTicket, IBM MFA): excellent at *what happens once you're on the mainframe*, weaker at *network-layer access in the first place*.
- **Generic ZTNA brokers** (Boundary, Teleport, Tailscale): designed for SSH and HTTPS, with little awareness of 3270 / TN3270 / EBCDIC / SNA semantics, and they require the backend to be *continuously reachable* through them.
- **Bastion-host + jump-server patterns**: operational toil, partial audit coverage, no native concept of "the door doesn't exist when nobody's authorized."

Cerberus fills the gap between them. Mainframe-native distribution (DASD volume on zLinux). Network-edge enforcement (ephemeral tunnel, not continuous exposure). Identity-source-agnostic (your AD/Okta/SAML *and* your RACF). Full audit trail. Drops into the operational model real mainframe shops already use.

The architecture isn't theoretical. Cerberus runs every day on a hobby z-Architecture stack: Win 11 → VMware Workstation Pro → zLinux for s390x → Hercules/Hyperion → MVS 3.8j TK5 and VM/370 Community Edition as parallel backends, with Cerberus gating both. The demo video shows it end to end.

---

## Commercial licensing

The community edition is free under the MIT-style license in [`LICENSE-COMMUNITY`](LICENSE-COMMUNITY). It is fully functional, fully documented, and the source for the commercial edition.

Commercial licensing for shops running real System z hardware includes:
- Pre-built zLinux DASD volume with everything configured and tested
- Defined support tiers (business-hours, 24×5, 24×7)
- Help with AD/LDAP/SAML/OIDC integration
- HA pair design and deployment assistance
- SIEM integration (Splunk, QRadar, ArcSight)
- Custom protocol surfaces (roadmap: SSH, HTTPS, RDP, VNC)
- Quarterly product reviews and roadmap input

**Contact: jimpames@gmail.com**

Tier pricing and a comparison matrix are in [`docs/commercial-tiers.md`](docs/commercial-tiers.md).

---

## Three things, before you close the tab

1. The endpoint really doesn't exist until you authenticate. We mean it. Try scanning the reserved address while no session is active. Nothing answers.
2. Cerberus complements RACF/ACF2/Top Secret &mdash; it does not replace them. RACF authenticates users to z/OS; Cerberus authenticates users to *the network path to z/OS*. Defense in depth.
3. We accept pull requests, bug reports, and pointed questions. We do not accept "this should be a SaaS" suggestions. It is intentionally not a SaaS. The customer keeps the data, the keys, the audit log, and the off switch.

---

<sub>MVS Cerberus &copy; 2026 jimpames. System z, z/OS, z/VM, RACF, ACF2, AS/400, and SYSTEM/36 are trademarks of International Business Machines Corporation. Hercules and Hyperion are projects of their respective communities. ngrok is a product of ngrok Inc. This project is not affiliated with or endorsed by any of the foregoing.</sub>
