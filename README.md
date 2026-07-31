# omega-federation-core

> **Description:** The primary orchestration daemon and runtime foundation for the Omega Federation. Implements a centralized asynchronous event bus, immutable SHA-3-256 event ledger, and a pluggable connector framework to synchronize disparate capabilities into a unified, auditable execution environment.

---

# Omega Federation Core

> **Commit 001 — Sovereign Runtime Foundation**
>
> A unified orchestration operating system. One daemon. One bus. Immutable truth.

## What This Is

`omega-federation-core` is the **single runtime** that powers the Omega Universe. Not a collection of separate tools, but one living daemon with internal modules communicating through a central event bus.

Every capability becomes a **connector**. Every event is **immutable**, hashed, and written to the ledger. The system can be **replayed, audited, resumed, verified**.

See [LINEAGE.md](LINEAGE.md) for the consolidation decision and history of the previous multi-engine material under this name.

## Architecture

```
omega start
↓
initialize runtime
↓
restore checkpoint
↓
load connectors
↓
start transport
↓
start federation bus
↓
begin listening
```

### The Bus Model

```
Transport ──► Bus ──► Permissions ──► Bus ──► Router ──► Bus ──► Connector ──► Bus ──► Ledger
```

Everything speaks only through the bus. Observable. Replayable. Recoverable.

### Components

| Module | File | Responsibility |
|--------|------|---------------|
| **Runtime** | `omega/core/runtime.py` | Main daemon, signal handling, lifecycle orchestration |
| **Bus** | `omega/core/bus.py` | Central async pub/sub event backbone |
| **Ledger** | `omega/core/ledger.py` | Immutable SHA-3-256 event log |
| **Checkpoint** | `omega/core/checkpoint.py` | State snapshots, restore, recovery |
| **Permissions** | `omega/core/permissions.py` | Capability-based access control |
| **Router** | `omega/core/router.py` | Event routing, dispatch, handler registry |
| **Supervisor** | `omega/core/supervisor.py` | Service start/stop/monitor/restart |
| **Connectors** | `omega/connectors/base.py` | Pluggable capability framework |
| **Transport** | `omega/transport/http.py` | HTTP ingress → Bus |
| **Transport** | `omega/transport/ws.py` | WebSocket ingress → Bus |
| **Federation** | `omega/federation/mesh.py` | Federation as a bus service |

## Quick Start

```bash
pip install -e .
python -m omega start --config omega/config.yaml
```

Health: `http://localhost:7777/health`  
WebSocket: `ws://localhost:7778`

## Omega Universe Position

| Repo | Layer | Role |
|------|-------|------|
| `omega-federation-core` | **Runtime (canonical)** | Unified orchestration daemon |
| `omega-federation-core-v2` | Runtime (clean parallel history) | Same foundation |
| `omega-brain-mcp` | Governance | Cortex gate, VERITAS pipeline |
| `veritas-vault` | Retention | Deterministic storage |
| `Aegis` | Policy | Sovereign access control |

## License

MIT — see `LICENSE` for full text.
