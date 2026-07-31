# Lineage — Omega Federation Core

## 2026-07-31 — Runtime Consolidation

This repository now hosts the **unified single-daemon runtime**.

Previous content under this name was a multi-engine conceptual monorepo
(Star / Aletheia / Omnissiah / KINGDOM / Alphabet orchestration scripts,
FastAPI surface, Termux deployment guides). That material remains in git
history and in sibling repositories.

### Why the change

The stated objective is one runnable place: a single process that can
absorb the rest of the Omega ecosystem as connectors and services.

The code now at the root of this repository is that process:

- One `OmegaRuntime` daemon
- One central `FederationBus`
- Immutable SHA-3-256 `EventLedger`
- Checkpoint / restore
- Capability-based permissions
- Pluggable connectors (filesystem, git, http_client)
- HTTP + WebSocket ingress under IngressAuthority

The parallel clean history lives at:
https://github.com/bekingdomcomejoker-cpu/omega-federation-core-v2

Both point at the same runtime foundation. This name is the canonical home.

### Absorption path

Other repositories in the account are not deleted. They become candidates
to be absorbed as connectors or bus services under this runtime.
