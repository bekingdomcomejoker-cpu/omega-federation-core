# Omega Termux Bridge + Codex on Termux
## Full Architecture, Troubleshooting & Recovery Log

**Date:** 2026-08-09  
**Environment:** Android / Termux, ARM64 (Redmi)  
**Outcome:** Both systems fully operational

---

## 1. Omega / Kai MCP Termux Bridge — Initial Architecture

A dependency-free MCP (Model Context Protocol) server was built to expose Termux capabilities over HTTP/JSON-RPC on localhost.

**File:** `~/omega_mcp_bridge.py`  
**Port:** `8787`  
**Transport:** Streamable HTTP + SSE keepalive  
**Tools exposed:**

- `termux_exec` — execute any shell command inside the Termux environment (with timeout)
- `network_snapshot` — read-only snapshot of interfaces, routes, DNS, listening ports, and default route

**Key design decisions:**
- Pure Python 3 standard library only (`http.server`, `subprocess`, `json`, etc.)
- Runs as `ThreadingHTTPServer` bound to `127.0.0.1:8787`
- Implements full MCP lifecycle: `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`
- Health endpoint at `/health`
- MCP endpoint at `/mcp` (GET for SSE stream, POST for JSON-RPC)

### Complete source (clean, production-ready)

```bash
cat > ~/omega_mcp_bridge.py <<'EOF'
#!/usr/bin/env python3

import json
import os
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8787
HOME = os.path.expanduser("~")


def send_json(h, status, obj, headers=None):
    data = json.dumps(obj).encode()
    h.send_response(status)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(data)))
    h.send_header("Cache-Control", "no-store")
    if headers:
        for k, v in headers.items():
            h.send_header(k, v)
    h.end_headers()
    h.wfile.write(data)


def rpc_error(req_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": code,
            "message": message
        }
    }


TOOLS = [
    {
        "name": "termux_exec",
        "description":
            "Execute a shell command in the user's Termux environment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute."
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds.",
                    "default": 30
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "network_snapshot",
        "description":
            "Read-only snapshot of the Termux device network state.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def run_command(command, timeout=30):
    try:
        timeout = max(1, min(int(timeout), 300))
    except Exception:
        timeout = 30

    try:
        p = subprocess.run(
            command,
            shell=True,
            cwd=HOME,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return (
            "EXIT CODE: %d\n\nSTDOUT:\n%s\nSTDERR:\n%s"
            % (
                p.returncode,
                p.stdout or "",
                p.stderr or ""
            )
        )

    except subprocess.TimeoutExpired:
        return "COMMAND TIMED OUT after %s seconds" % timeout

    except Exception as e:
        return "EXECUTION ERROR: %r" % e


def network_snapshot():
    command = r'''
echo "=== TIME ==="
date

echo
echo "=== INTERFACES ==="
ip -brief addr 2>&1 || true

echo
echo "=== ROUTES ==="
ip route 2>&1 || true

echo
echo "=== DNS ==="
getprop 2>/dev/null | grep -E 'net\.dns|net\.hostname' | head -30 || true

echo
echo "=== LISTENING PORTS ==="
ss -lntup 2>&1 | head -60 || true

echo
echo "=== DEFAULT ROUTE ==="
ip route get 1.1.1.1 2>&1 || true
'''
    return run_command(command, 30)


class Handler(BaseHTTPRequestHandler):

    server_version = "Omega-Termux-MCP/2.0"

    def log_message(self, fmt, *args):
        print("[Ω MCP]", fmt % args, flush=True)

    def do_GET(self):

        if self.path == "/health":
            send_json(self, 200, {
                "ok": True,
                "service": "omega-termux-mcp",
                "transport": "streamable-http",
                "port": PORT
            })
            return

        if self.path == "/mcp":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            try:
                self.wfile.write(b": omega-termux-mcp connected\n\n")
                self.wfile.flush()

                while True:
                    time.sleep(15)
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()

            except (BrokenPipeError, ConnectionResetError):
                pass

            return

        send_json(self, 404, {"error": "not found"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Accept, Authorization, Mcp-Session-Id"
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )
        self.end_headers()

    def do_POST(self):

        if self.path != "/mcp":
            send_json(self, 404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length > 1024 * 1024:
                send_json(self, 413, {"error": "request too large"})
                return

            raw = self.rfile.read(length)
            req = json.loads(raw.decode("utf-8"))

        except Exception as e:
            send_json(
                self,
                400,
                rpc_error(None, -32700, "Invalid JSON: %s" % e)
            )
            return

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}

        if method == "initialize":
            session_id = str(uuid.uuid4())
            result = {
                "protocolVersion": params.get("protocolVersion", "2025-03-26"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "omega-termux", "version": "2.0.0"},
                "instructions": "Omega Termux command and network bridge."
            }
            send_json(
                self, 200,
                {"jsonrpc": "2.0", "id": req_id, "result": result},
                {"Mcp-Session-Id": session_id, "Access-Control-Allow-Origin": "*"}
            )
            return

        if method == "notifications/initialized":
            self.send_response(202)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return

        if method == "ping":
            send_json(
                self, 200,
                {"jsonrpc": "2.0", "id": req_id, "result": {}},
                {"Access-Control-Allow-Origin": "*"}
            )
            return

        if method == "tools/list":
            send_json(
                self, 200,
                {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}},
                {"Access-Control-Allow-Origin": "*"}
            )
            return

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}

            if name == "network_snapshot":
                text = network_snapshot()
            elif name == "termux_exec":
                command = arguments.get("command")
                if not isinstance(command, str) or not command.strip():
                    send_json(self, 200, rpc_error(req_id, -32602, "command is required"))
                    return
                text = run_command(command, arguments.get("timeout", 30))
            else:
                send_json(self, 200, rpc_error(req_id, -32601, "Unknown tool: %s" % name))
                return

            send_json(
                self, 200,
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": text}]
                    }
                },
                {"Access-Control-Allow-Origin": "*"}
            )
            return

        send_json(
            self, 200,
            rpc_error(req_id, -32601, "Method not found: %s" % method)
        )


print("========================================")
print(" Ω OMEGA TERMUX MCP BRIDGE")
print("========================================")
print("HTTP:   http://127.0.0.1:%d/mcp" % PORT)
print("Health: http://127.0.0.1:%d/health" % PORT)
print("Mode:   dependency-free")
print("========================================")

server = ThreadingHTTPServer((HOST, PORT), Handler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
EOF
```

### Validation & Startup

```bash
python3 -m py_compile ~/omega_mcp_bridge.py   # must return nothing
python3 ~/omega_mcp_bridge.py
```

Expected banner:

```
========================================
 Ω OMEGA TERMUX MCP BRIDGE
========================================
HTTP:   http://127.0.0.1:8787/mcp
Health: http://127.0.0.1:8787/health
Mode:   dependency-free
========================================
```

This bridge is the local control plane for Termux command execution and network state.

---

## 2. Codex on Termux — Troubleshooting & Recovery

### Initial problem

Codex OAuth login failed:

```
Token exchange error: error sending request for url (https://auth.openai.com/oauth/token)
Error logging in: Token exchange failed...
```

### Network & platform verification

- DNS, IPv4, TLS 1.3, certificate validation, and system time all correct.
- Node v26.4.0 networking worked.
- Codex package 0.147.0 is a thin Node wrapper that launches a **native Linux musl binary**:

```
/data/data/com.termux/files/usr/lib/node_modules/@openai/codex-linux-arm64/vendor/aarch64-unknown-linux-musl/bin/codex
```

(~212 MB, statically linked ELF aarch64)

### Root cause

The native musl binary expects conventional Linux paths:

- `/etc/resolv.conf`
- `/etc/ssl/certs/ca-certificates.crt`

Termux stores them under `$PREFIX`:

- `$PREFIX/etc/resolv.conf`
- `$PREFIX/etc/tls/cert.pem`

### Fix — proot bind mounts

```bash
proot \
  -b "$PREFIX/etc/resolv.conf:/etc/resolv.conf" \
  -b "$PREFIX/etc/tls/cert.pem:/etc/ssl/certs/ca-certificates.crt" \
  "$CODEX_BIN" login --device-auth
```

Device-code auth succeeded and produced a valid ChatGPT login.

### Persistent wrapper

```bash
mkdir -p ~/bin

cat > ~/bin/codex-linux <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
CODEX_BIN="$PREFIX/lib/node_modules/@openai/codex-linux-arm64/vendor/aarch64-unknown-linux-musl/bin/codex"
exec proot \
  -b "$PREFIX/etc/resolv.conf:/etc/resolv.conf" \
  -b "$PREFIX/etc/tls/cert.pem:/etc/ssl/certs/ca-certificates.crt" \
  "$CODEX_BIN" "$@"
EOF

chmod +x ~/bin/codex-linux
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verification:

```bash
codex-linux --version          # codex-cli 0.147.0
codex-linux login status       # Logged in using ChatGPT
```

End-to-end agent test (read-only directory inspection) succeeded.

---

## 3. Final Working State

| Component              | Status | Command / Endpoint                     |
|------------------------|--------|----------------------------------------|
| Omega MCP Bridge       | ✅     | `python3 ~/omega_mcp_bridge.py`        |
| MCP HTTP               | ✅     | `http://127.0.0.1:8787/mcp`            |
| Health                 | ✅     | `http://127.0.0.1:8787/health`         |
| Codex CLI              | ✅     | `codex-linux`                          |
| Codex Auth             | ✅     | ChatGPT device-auth                    |
| Native binary via proot| ✅     | Bind-mounted resolv + CA               |

**Architecture summary**

```
Termux (Android)
├── Omega MCP Bridge (Python, :8787)
│     ├── termux_exec
│     └── network_snapshot
└── Codex (native musl binary via proot)
      ├── /etc/resolv.conf      ← bind $PREFIX/etc/resolv.conf
      └── /etc/ssl/certs/...    ← bind $PREFIX/etc/tls/cert.pem
```

Both systems are now stable and ready for federation use.
