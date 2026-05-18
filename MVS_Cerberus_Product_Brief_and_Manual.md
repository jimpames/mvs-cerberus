# MVS CERBERUS
### 3270 RADIUS Turret Firewall for System/390 and Hercules/Hyperion

> *Ephemeral access. Audited sessions. Zero firewall configuration.*
> *The door doesn't exist until you've authenticated.*

---

## What MVS Cerberus Is

MVS Cerberus is an **authenticated edge gateway** for 3270 terminal access to mainframe systems. It sits between your users and your mainframes, opens an ephemeral TN3270 path only after a user successfully authenticates, closes that path the moment their session lease expires, and produces a complete audit record of every connection it ever brokered.

It is distributed as a **ready-to-IPL DASD volume** containing a hardened zLinux 18.04 for System/390, with Cerberus, ngrok, Python, and Go preinstalled and pre-configured. Attach the DASD. IPL it. Configure your auth source. You have a working 3270 access control plane.

There is nothing to install in the conventional sense. The product is a disk image.

---

## What It Replaces

| Current pain | MVS Cerberus answer |
|---|---|
| TN3270 ports continuously exposed to your internal network or DMZ | Ports only listen during authenticated sessions; absent the rest of the time |
| Static firewall rules, NAT mappings, and bastion hosts to broker access | Zero firewall configuration; the gateway summons the path on demand |
| Heterogeneous audit trails across emulator clients, TN3270 servers, and jump hosts | One canonical audit log of every grant, session, disconnect, and revocation |
| Auth tied exclusively to RACF/ACF2/Top Secret, hard to integrate with corporate IDP | RADIUS, LDAP/AD, SAML 2.0, and OIDC upstream; PassTicket pass-through to RACF for final authorization |
| Per-LPAR access management at the operating system layer only | Network-layer enforcement that complements rather than competes with RACF |
| Compliance evidence assembled manually from disparate logs | SIEM-ready audit feed in syslog, CEF, and JSON formats |

---

## The Security Philosophy

Most network access products try to keep attackers out. They sit *in front of* the protected service, watch traffic, and reject what shouldn't pass. The service is reachable; the defense is active inspection.

MVS Cerberus inverts the model. **The default state is that no listener exists.** A port scan against your reserved endpoint returns nothing. Reconnaissance against your 3270 ports finds nothing to map. There is no attack surface to enumerate, because the surface itself is summoned into existence only by successful authentication, and dismissed when the lease expires.

This is sometimes called *just-in-time access* or *zero-standing-exposure*. We call it **the door isn't there until you knock**.

Implications:

- **CVEs in the protected backend are not internet-exposed.** A new mainframe TCP/IP defect cannot be opportunistically exploited because there is no continuously listening port to target.
- **Reconnaissance is structurally crippled.** Attackers cannot discover the existence of, let alone fingerprint, the systems behind Cerberus through normal scanning.
- **Lateral movement is bounded by lease.** A compromised user session reaches one backend, for the remaining duration of one lease, and ends.
- **Audit completeness is structural.** Because Cerberus brokers the path itself, no access can occur without Cerberus knowing about it. There is no "this LPAR got reached and we don't know how."

---

## Architecture

```
        Authorized User
              │
              ▼
   ┌──────────────────────────┐
   │   Cerberus Web Auth      │  ← persistent HTTPS endpoint
   │   (auth.your-domain)     │
   └─────────────┬────────────┘
                 │  RADIUS / LDAP / SAML / OIDC / PassTicket
                 ▼
   ┌──────────────────────────┐
   │   Cerberus Gate          │  ← grant decisions, session policy
   │   - Identity validation  │
   │   - Authorization check  │
   │   - Lease management     │
   │   - Audit emission       │
   └─────────────┬────────────┘
                 │  grant event
                 ▼
   ┌──────────────────────────┐
   │   Cerberus Turret        │  ← ephemeral exposure layer
   │   - Per-session tunnel   │     (TN3270 over reserved TCP)
   │   - Time-boxed lifecycle │
   │   - Idle-timeout enforce │
   └─────────────┬────────────┘
                 │
                 ▼
   ┌──────────────────────────┐
   │   Your Mainframes        │
   │   - z/OS LPARs           │
   │   - VM LPARs             │
   │   - Hercules/Hyperion    │
   │   - Multiple backends    │
   │     selected from menu   │
   └──────────────────────────┘
```

Cerberus runs in a Linux LPAR (real System z hardware via an IFL engine) or in a Hercules/Hyperion environment for development, validation, and lab use. It operates entirely within your infrastructure boundary. There is no vendor cloud dependency for control-plane functions.

---

## What's in the DASD

You receive one DASD volume. Attach it to a Hercules instance or to an IFL on real System z hardware. It contains:

- **zLinux 18.04 for System/390** — hardened base operating system, configured for IPL from this volume
- **Cerberus Gate v2.0** — the policy engine, written in Python, runnable as a systemd service
- **Cerberus Turret** — the ephemeral exposure binary, written in Go, statically linked
- **Embedded RADIUS server** — for environments without a separate RADIUS infrastructure
- **ngrok agent** — pre-configured for reserved TCP/HTTPS endpoint use; bring your own authtoken
- **SQLite session store** — for audit records and active leases
- **Web admin interface** — for user management, backend registration, and lease monitoring
- **Sample configuration** — `/etc/cerberus/cerberus.ini` and `/etc/cerberus/environment` ready for editing

Configuration is the customer's. Secrets are the customer's. Identity is the customer's. The image contains no embedded credentials and no phone-home behavior.

---

## Deployment Modes

**Mode 1 — Hercules/Hyperion lab.** Drop the CCKD onto disk next to your existing TK5, TK4-, or VM/370 CE volumes. Add one device line to your hercules.cnf at any free virtual device address. IPL Cerberus, configure your backends, validate end-to-end. Recommended starting point for evaluation, training, and tabletop exercise environments.

**Mode 2 — IFL on real System z.** Define a Linux guest under z/VM or as an LPAR. Attach the DASD as the IPL volume. Bring up Cerberus inside your production environment. Integrate with corporate identity sources. Begin gating real 3270 traffic. The intended production deployment for commercial customers.

**Mode 3 — Air-gapped enterprise.** Same as Mode 2, with ngrok replaced by an internal-only reverse proxy or VPN-mediated tunnel. Some assembly required for the internal exposure plane; supported via custom services agreement.

---

## Supported Backend Systems

Cerberus is protocol-agnostic at the TN3270 layer. It works with anything that speaks the 3270 datastream:

- **z/OS** — TSO, ISPF, CICS, IMS, NetView
- **z/VM** — CMS, all VM guests reachable via SNA or TN3270
- **z/VSE** — CICS/VSE, ICCF, POWER
- **VM/370 Community Edition** — for vintage operations and training
- **MVS 3.8J (TK5, TK4-, custom builds)** — for hobby and educational use
- **Hercules/Hyperion** of any flavor running any of the above
- **CICS Web Support gateways**, **IMS Connect**, **legacy Telnet 3270** services
- **Anything else** that listens on TCP and speaks 3270 datastream

Multiple backends are registered in a single Cerberus instance. Authenticated users select from a menu at grant time. Authorization rules can restrict which users may reach which backends.

---

## Identity and Audit

**Identity sources supported:**

- RADIUS (embedded server included; can also forward to existing RADIUS infrastructure)
- LDAP / Active Directory
- SAML 2.0
- OpenID Connect (OIDC)
- IBM PassTicket (for shops where RACF should remain the authoritative authenticator)
- Local user database (for air-gapped or initial-bootstrap configurations)

**Audit events emitted:**

- Authentication attempt (success and failure, with source IP and user agent)
- Authorization decision (which backend, which user, which policy matched)
- Grant issued (lease ID, duration, backend, source IP)
- Session established (tunnel open, backend connect confirmed)
- Session activity (idle warnings, lease extensions, voluntary disconnects)
- Session terminated (lease expiry, administrative revocation, anomaly response)
- Configuration changes (user added, backend registered, policy updated)

**Export formats:**

- Syslog (RFC 5424, with structured data)
- Common Event Format (CEF) for SIEM ingestion
- JSON Lines for direct file consumption
- IBM QRadar DSM-compatible format

---

## Compliance Posture

Cerberus produces audit evidence aligned with the controls most frequently cited during financial-services and government audits:

- **PCI-DSS** — requirements 7 (access control), 8 (authentication), 10 (logging and monitoring)
- **SOX** — IT general controls around access provisioning and review
- **FFIEC** — Cybersecurity Assessment Tool, access management domain
- **GDPR** — Article 32 (security of processing), access logging
- **FedRAMP** — AC-2, AC-3, AC-17, AU-2 control families (for government deployments)
- **NIST 800-53** — AC, AU, IA control families

Cerberus does not, by itself, certify a customer to any of these frameworks. It provides the technical control evidence that auditors expect to see when 3270 access is in scope.

---

## Pricing Model

Pricing is per Cerberus instance (LPAR or Hercules host), per year, including support and updates.

| Tier | Annual | What's included |
|---|---|---|
| **Community** | Free | DASD volume, community support via mailing list, one Cerberus instance, suitable for hobby and lab use |
| **Small Shop** | $12,000 | Two production instances, business-hours email support, basic audit-to-syslog, AD/LDAP integration |
| **Mid-Market** | $48,000 | Up to ten instances, 24×5 support, SIEM integration, SAML/OIDC, HA pair configuration, quarterly check-ins |
| **Enterprise** | Custom | Unlimited instances, 24×7 support, custom integrations, dedicated support engineer, on-site enablement |

Customer-supplied infrastructure: System z hardware (or Hercules host), an IFL engine or LPAR allocation, an identity source, and an exposure mechanism (ngrok account or equivalent internal reverse proxy).

Customer keeps all data. Customer keeps all configuration. Customer keeps all identity material. Cerberus phones home for nothing.

---

## Frequently Asked Questions

**Q: Is this a replacement for RACF, ACF2, or Top Secret?**
No. Those products authenticate users to the mainframe operating system. Cerberus gates *network access to the mainframe in the first place*. Defense in depth. They operate at different layers and complement each other. Cerberus can optionally use RACF PassTicket for inline authentication when that posture is preferred.

**Q: Does Cerberus require IBM software licenses?**
No additional licenses beyond what you already operate. Cerberus runs on Linux for IBM Z, which Red Hat, SUSE, and Canonical license separately if you choose a commercial Linux distribution. The included zLinux is a community build of Ubuntu 18.04 for s390x, freely redistributable.

**Q: What happens if Cerberus itself fails?**
Existing granted sessions continue (the ephemeral tunnels are independent processes). New grants cannot be issued until Cerberus is restored. HA pair configurations eliminate this single point of failure.

**Q: How is the DASD volume delivered?**
Encrypted download from a customer portal, plus a hash signed by Cerberus's release key. Air-gapped customers can request physical media.

**Q: What's the update process?**
A new release ships as a new DASD volume. Configuration persists in a separate config minidisk that survives volume replacement. Production customers test in their lab Hercules environment before swapping the production volume.

**Q: Can it gate non-3270 protocols?**
Future versions, yes. The architecture is protocol-agnostic. SSH, HTTPS, RDP, and Telnet support are on the roadmap. The 3270 surface is the first commercial release because that is the underserved market today.

**Q: Why a DASD volume and not a Docker container or OVA?**
Because mainframe shops operate DASD volumes. Docker on z/OS is a specialized story. OVAs are vSphere-centric. A DASD image speaks the operational language your sysprogs already know. We deliver in the format your team already understands.

**Q: What if our internal compliance forbids ngrok or any third-party tunnel service?**
The exposure plane is pluggable. Cerberus can drive raw iptables/nftables rules, WireGuard peer authorization, or a customer-supplied internal reverse proxy in place of ngrok. The control plane is unchanged.

**Q: Is the source code available?**
The Community tier ships with full source. Commercial tiers receive source under a commercial license. We do not ship binaries without corresponding source to enterprise customers, because we expect them to audit what runs in their environment.

**Q: What if the vendor goes away?**
Source is in customer hands. The DASD volume runs without external dependencies. Customer can fork, maintain, and operate indefinitely. This is intentional design for mainframe procurement risk profiles.

---

## Operator Quick Start

After receiving the DASD volume:

```text
1.  Attach the volume to your Hercules or LPAR configuration.
2.  IPL it.
3.  Log in as the documented bootstrap account.
4.  Edit /etc/cerberus/environment with your ngrok token (or 
    internal exposure mechanism credentials) and a strong 
    CERBERUS_RADIUS_SECRET and CERBERUS_SECRET_KEY.
5.  Edit /etc/cerberus/cerberus.ini to register your backend 
    systems (hostname, port, friendly name) and configure your 
    upstream identity source.
6.  Run: /opt/cerberus/bringupall.sh
7.  Browse to https://your-reserved-domain/ and authenticate.
8.  Select a backend from the menu. Receive your granted endpoint.
9.  Point your TN3270 client at the granted endpoint.
10. Watch the audit log to confirm the entire flow recorded.
```

Production deployments add identity federation, HA, SIEM integration, and policy refinement. The above is the lab bring-up. The walkthrough included with the DASD covers production deployment step-by-step.

---

## About the Project

MVS Cerberus is developed and maintained by a working engineer who runs hobby mainframes at home and saw a gap in how their access is gated. The 3270 access problem at commercial scale turned out to be the same problem, with the same answer, applied with more rigor. The DASD-distribution model mirrors how IBM has shipped operating system program products since 1964, because that is the operational language mainframe shops speak.

The community version of MVS Cerberus is open source. The commercial tiers are software-product offerings with support and update obligations. Both are built from the same codebase. Hobbyist contributors and commercial customers reinforce each other rather than compete.

---

## Contact

For licensing, evaluation downloads, and support:

**`jimpames@gmail.com`**

For source code and community discussion:

**GitHub: `jimpames/mvs-cerberus`**

For demonstration videos and walkthroughs:

**YouTube: MVS Cerberus channel**

---

> *MVS CERBERUS — three heads at the gate.*
> *Hack the net all you want. The tunnel to admin is Cerberus only, and down till authed.*

<sub>© 2026 — Distributed under separate community and commercial license terms. System z, z/OS, z/VM, z/VSE, and RACF are trademarks of International Business Machines Corporation. Hercules and Hyperion are projects of their respective communities. ngrok is a product of ngrok Inc.</sub>
