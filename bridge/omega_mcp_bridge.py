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
