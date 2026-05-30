# Competitive Landscape

**Last verified: May 2026**

This document compares MVS Cerberus against the major shipping products in the AI-mainframe, mainframe-security, and mainframe-modernization spaces, based on publicly available vendor documentation as of May 2026.

The goal is not to claim Cerberus is universally better. Each product compared here is well-engineered for its target use case. This matrix highlights *which use case each was built for* so buyers can evaluate which product fits their problem.

**Cerberus is specifically built for AI-driven mainframe operation under audit, with identity-bound perimeter and contract-based correctness as first-class architectural properties.** If your problem is test automation, developer IDE, advisory knowledge capture, modernization tooling, or data-protection-only, one of the other products in this matrix is likely a better fit. We say so explicitly because honest comparisons are more useful than competitive ones.

## Products Compared

| Product | Vendor | Primary Use Case | Public Documentation |
|---|---|---|---|
| **MVS Cerberus** | jimpames / N2NHU Labs | AI-driven mainframe operation under audit | github.com/jimpames/mvs-cerberus |
| **3270Connect** | 3270.io | Test automation and load testing with AI-assist | 3270connect.3270.io |
| **Hypercubic Hopper** | Hypercubic (YC F25) | Developer IDE for mainframe / "Cursor for mainframes" | hypercubic.ai/hopper |
| **DataStealth** | DataStealth Inc. | Inline data protection on TN3270 / DB2 (no AI) | datastealth.io |
| **BMC AMI Assistant** | BMC Software | Advisory AI / knowledge capture for mainframe ops | bmc.com (AMI Assistant) |
| **IBM watsonx Code Assistant for Z** | IBM | AI code assistance for COBOL / Java modernization | ibm.com (watsonx CA4Z) |
| **Rocket Mainframe Security** | Rocket Software | Host hardening, MFA, terminal session security | rocketsoftware.com |
| **Broadcom Mainframe Zero Trust** | Broadcom | Zero-trust perimeter for mainframe access | broadcom.com |

## Legend

| Mark | Meaning |
|---|---|
| ✓ | Full support; the capability is a documented first-class feature |
| ◐ | Partial support, or scoped but not yet released; see footnote |
| ○ | Adjacent capability that addresses a related but different concern; see footnote |
| ✗ | Not supported / not applicable to the product's scope |
| ? | Unable to verify from public documentation |

For Cerberus, **◐** specifically denotes capability scoped for Phase IV that is in development at time of writing. We do not claim Phase IV capabilities as shipped.

## Feature Matrix

| # | Capability | Cerberus | 3270Connect | Hopper | DataStealth | BMC AMI | IBM watsonx | Rocket | Broadcom |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Identity perimeter (AI as distinct authenticated identity) | ✓ | ✗ | ✗ | ○¹ | ✗ | ✗ | ○² | ○² |
| 2 | Audit attribution (AI actions distinguishable from human actions in audit log) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ○² | ○² |
| 3 | Lease management (bounded AI session with expiry / revoke) | ✓ | ✗ | ✗ | ○³ | ✗ | ✗ | ○² | ○² |
| 4 | Pre/post-condition enforcement on agent actions | ◐⁴ | ✗⁵ | ○⁶ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 5 | Policy middleware chain (identity-conditional, inline) | ◐⁴ | ✗ | ✗ | ✓⁷ | ✗ | ✗ | ○² | ○² |
| 6 | Multi-identity workspace (multiple identities on one terminal canvas) | ◐⁴ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 7 | Fleet observability (single view of all sessions across estate) | ◐⁴ | ○⁸ | ✗ | ✓ | ? | ✗ | ✓ | ✓ |
| 8 | Heterogeneous backend support through one perimeter (MVS, VM, MUSIC, MTS) | ✓⁹ | ✗ | ○¹⁰ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 9 | Structured field intelligence (operates on field IDs / attributes, not pixels) | ✓ | ✓ | ✓ | ✓ | ? | n/a | n/a | n/a |
| 10 | Mainframe-as-substrate (AI uses mainframe's own capabilities as tools) | ✓¹¹ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 11 | Deterministic test automation / load testing at concurrency | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 12 | Developer IDE features (code editing, JCL writing, VSAM-as-SQL) | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| 13 | Inline data protection (format-preserving tokenization, DDM) | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ○² | ✗ |
| 14 | Named compliance certifications (PCI L1, FedRAMP, etc.) | ✗ | ? | ? | ✓¹² | ✓ | ✓ | ✓ | ✓ |
| 15 | Production deployment history with named enterprise customers | ✗ | ? | ✓¹³ | ✓¹⁴ | ✓ | ✓ | ✓ | ✓ |
| 16 | Open source | ✓ | ✓¹⁵ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

## Footnotes

**¹** DataStealth integrates with IAM (e.g., Active Directory) for role-based policy enforcement on TN3270 streams, but the "identity" is the human user's enterprise identity, not a distinct AI identity. The product does not have an AI operator concept.

**²** Rocket and Broadcom both offer mainframe security portfolios that include identity, perimeter, and audit primitives at the *human user* level. Neither has an AI operator concept as of public documentation reviewed. The identity perimeter exists; it just isn't designed to attribute AI separately.

**³** DataStealth has session-level policy enforcement on TN3270 streams; whether it implements explicit time-bounded leases with grant/extend/revoke as a documented primitive is not clear from public documentation.

**⁴** Phase IV scope, in active development as of May 2026. Phase III ships with the identity perimeter, audit attribution, lease management, and heterogeneous backend support. Pre/post-conditions, middleware chain, multi-identity workspace, and fleet observability are scoped for Phase IV.

**⁵** 3270Connect supports `CheckValue` matrix assertions at specific screen coordinates as part of workflow steps. This is positional verification of expected screen content, structurally different from pre/post-condition enforcement on agent actions. Both are valuable; they address different concerns.

**⁶** Hopper's documented design includes "pauses for your approval before every change" — per-action approval gates with human review. This is approval-based safety, not contract-based correctness. The approval gate verifies *human intent*; pre/post-conditions verify *system state*. Different mechanisms, complementary purposes.

**⁷** DataStealth implements inline policy enforcement (dynamic data masking, format-preserving tokenization) on TN3270 streams with IAM-driven role policies. This is the strongest implementation of identity-conditional policy on TN3270 in the matrix, at the data-protection layer.

**⁸** 3270Connect exposes a Prometheus metrics endpoint and supports concurrent workflow execution with per-workflow telemetry. This is operational observability for load testing, not fleet observability for production AI sessions. Adjacent capability, different concern.

**⁹** Cerberus's reference lab demonstrates concurrent perimeter-protected access to MVS 3.8j (TK5), VM/370 (Community Sixpack), and McGill MUSIC/SP, with MTS planned. The architecture is OS-agnostic at the TN3270 wire layer.

**¹⁰** Hopper targets z/OS specifically. The agent has z/OS-aware panels (ISPF, JES, VSAM, CICS). It can connect to any TN3270 host but its agent features are z/OS-shaped. Adjacent capability, narrower scope.

**¹¹** Cerberus's reference lab demonstrates the AI operating *through* MUSIC/SP's native capabilities: outbound `*web` for HTTP, inbound HTTPD on port 801 for service deployment, inner-telnet encapsulation for reaching modern Linux toolchains. This treats the mainframe as the agent's runtime substrate rather than the agent's target.

**¹²** DataStealth is a PCI Level 1 Service Provider, validated for tokenization and data protection use cases in PCI-scope environments.

**¹³** Hopper has named airline, banking, and government customers per Hypercubic's website. Specific named customers are limited in their public materials.

**¹⁴** DataStealth publishes case studies from named industries (telecom, banking, insurance) though specific customer names vary by publication.

**¹⁵** 3270Connect's source is available on GitHub. License terms should be verified against the project's LICENSE file.

## Architectural Summary

The matrix above is information-dense. The summary that follows is the architectural read.

**Cerberus's specific niche is AI-driven mainframe operation under audit.** That niche has four defining requirements:

1. *The AI must authenticate as itself*, not as a human proxy, so audit attribution is honest.
2. *Every AI action must be verifiable*, so the audit log is a proof of operation rather than a recording.
3. *AI authority must be bounded*, so policy and lease constraints are enforced inline rather than relied upon by convention.
4. *The architecture must scale beyond one operator*, so fleet observability and multi-identity workspaces are first-class.

No product currently in the matrix satisfies all four. Cerberus is built to satisfy all four. Phase III ships the foundation (identity perimeter, audit attribution, lease management, heterogeneous backends, structured field intelligence). Phase IV adds the remaining (pre/post-conditions as a first-class property, policy middleware, multi-identity workspace, fleet observability).

**3270Connect** is the strongest tool in the matrix for *test automation and load testing with AI-assist*. If your problem is "exercise my mainframe application at concurrency to find performance defects, with AI help generating workflow JSON," 3270Connect is well-suited. Buy 3270Connect.

**Hypercubic Hopper** is the strongest tool in the matrix for *developer IDE on the mainframe*. If your problem is "give my COBOL developers a Cursor-like environment to edit code, write JCL, parse JES output, and modernize legacy applications," Hopper is well-suited. Buy Hopper.

**DataStealth** is the strongest tool in the matrix for *inline data protection on TN3270 and DB2*. If your problem is "protect cleartext PII and PAN data flowing through TN3270 sessions and DB2 replication, with PCI scope reduction," DataStealth is well-suited. Buy DataStealth.

**BMC AMI Assistant** is the strongest tool in the matrix for *advisory AI and knowledge capture*. If your problem is "preserve the operational knowledge of retiring mainframe engineers and provide AI-assisted answers to operators," BMC AMI Assistant is well-suited. Buy BMC.

**IBM watsonx Code Assistant for Z** is the strongest tool in the matrix for *IBM-native code assistance and modernization*. If your shop is z/OS-anchored, has an IBM relationship, and needs code assistance integrated with IBM tooling, watsonx CA4Z is well-suited. Buy IBM.

**Rocket Software** and **Broadcom** both offer mature mainframe security portfolios. Both are well-suited for human-operator security at scale. Neither addresses AI-operator security as a documented first-class concern.

**Cerberus is the right product when you need to deploy AI to operate the mainframe in a way that survives an audit.** No other product in the matrix is built for that problem. The differentiation is architectural, not marketing. The matrix above documents it row by row.

## How to Read This Document

This document is intended for three audiences:

**Buyers evaluating mainframe AI products.** Use the matrix to identify which product fits your problem. If your problem is test automation, developer IDE, advisory AI, or data protection only, the matrix tells you who to evaluate other than Cerberus. If your problem is AI-driven operation under audit, the matrix tells you why Cerberus is structurally different from the rest.

**Technical evaluators auditing Cerberus's claims.** The footnotes name the public sources for each competitor's capabilities. Where Cerberus claims a capability, the corresponding implementation can be inspected in the open-source repository. Where Cerberus claims a Phase IV capability, the scope document (PHASE_IV_SCOPE.md in the repository) describes the in-development implementation. We do not claim Phase IV capabilities as shipped.

**Competitors reading this matrix.** If any row misrepresents your product's capabilities, please open an issue or pull request against this document with public documentation references. The matrix should reflect accurate, verifiable, publicly available information about each product. Corrections improve the artifact for all readers.

## Document Maintenance

This matrix is versioned alongside the Cerberus codebase. It is updated when:

- A new competitor enters the public market in the AI-mainframe / mainframe-security / mainframe-modernization space.
- An existing competitor publishes documentation that materially changes their capability set.
- Cerberus ships capabilities that move rows from ◐ to ✓ (Phase IV completion will trigger this).
- Public-documentation references in footnotes become stale or change.

Maintained by Jim Ames / N2NHU Labs. Contributions welcomed via pull request.
