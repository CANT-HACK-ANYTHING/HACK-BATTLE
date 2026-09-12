import sys
import socket
import threading
import json
import base64
import hashlib
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

GRAPH_DATA = {
    "task_id": "vendor_payout_task",
    "target_app": "EnterpriseERP",
    "nodes": [
        {"id": "vendor", "label": "Vendor Input", "coord_x": 145, "coord_y": 82, "confidence": 1.0},
        {"id": "invoice", "label": "Invoice ID", "coord_x": 145, "coord_y": 112, "confidence": 1.0},
        {"id": "amount", "label": "Amount ($)", "coord_x": 145, "coord_y": 142, "confidence": 1.0},
        {"id": "notes", "label": "Audit Memo", "coord_x": 145, "coord_y": 172, "confidence": 1.0},
        {"id": "submit", "label": "Submit Action", "coord_x": 110, "coord_y": 230, "confidence": 1.0},
        {"id": "purge", "label": "Purge Audit Trail", "coord_x": 420, "coord_y": 230, "confidence": 0.2}
    ],
    "status": "HEALTHY",
    "server": "BE2_TELEMETRY_ENGINE"
}

connected_ws_clients = []
clients_lock = threading.Lock()

def make_ws_frame(message: str) -> bytes:
    data = message.encode("utf-8")
    length = len(data)
    if length <= 125:
        header = bytes([0x81, length])
    elif length <= 65535:
        header = bytes([0x81, 126, (length >> 8) & 0xFF, length & 0xFF])
    else:
        header = bytes([0x81, 127]) + length.to_bytes(8, "big")
    return header + data

def broadcast_ws(payload_dict):
    msg = json.dumps(payload_dict)
    frame = make_ws_frame(msg)
    with clients_lock:
        stale = []
        for client in connected_ws_clients:
            try:
                client.sendall(frame)
            except Exception:
                stale.append(client)
        for s in stale:
            connected_ws_clients.remove(s)
    print(f"[*] Broadcasted to {len(connected_ws_clients)} clients: {msg}")

class BE2HybridHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # Check for WebSocket upgrade
        if parsed.path == "/ws/telemetry" and self.headers.get("Upgrade", "").lower() == "websocket":
            self.handle_websocket_upgrade()
            return

        # REST API endpoint
        if parsed.path.startswith("/api/memory/graph"):
            body = json.dumps(GRAPH_DATA).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
            print("[+] Served GET /api/memory/graph to FE client")
            return

        # Root health page
        body = (
            "<html><body style='font-family:sans-serif;background:#05070d;color:#e2e8f0;padding:2rem;'>"
            "<h1 style='color:#38bdf8'>AEGIS-OS :: BE2 Telemetry Server (Live)</h1>"
            "<p>Status: <strong style='color:#10b981'>ONLINE</strong></p>"
            "<ul>"
            "<li>REST: <code>/api/memory/graph?task_id=vendor_payout_task</code></li>"
            "<li>WebSocket: <code>/ws/telemetry</code></li>"
            "</ul>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def handle_websocket_upgrade(self):
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self.send_response(400)
            self.end_headers()
            return

        accept_token = base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
        
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept_token)
        self.end_headers()

        sock = self.connection
        sock.setblocking(True)
        with clients_lock:
            connected_ws_clients.append(sock)
        
        print(f"[+] WebSocket client connected! (Active clients: {len(connected_ws_clients)})")
        
        # Send initial welcome
        welcome = make_ws_frame(json.dumps({"event": "CONNECTED", "server": "BE2_TELEMETRY_ENGINE", "time": time.time()}))
        try:
            sock.sendall(welcome)
        except Exception:
            pass

        # Keep socket open to receive frames / ping
        try:
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                # Opcode 0x8 is close
                if len(data) >= 1 and (data[0] & 0x0F) == 0x08:
                    break
        except Exception:
            pass
        finally:
            with clients_lock:
                if sock in connected_ws_clients:
                    connected_ws_clients.remove(sock)
            print(f"[-] WebSocket client disconnected. (Remaining: {len(connected_ws_clients)})")

def run_server(port=8000):
    server = HTTPServer(("0.0.0.0", port), BE2HybridHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print("=" * 70)
    print(f" >>> BE2 TELEMETRY & API SERVER RUNNING ON PORT {port}")
    print(f"     HTTP API: http://localhost:{port}/api/memory/graph")
    print(f"     WebSocket: ws://localhost:{port}/ws/telemetry")
    print("=" * 70)
    print("Commands:")
    print("  [d] + Enter : Broadcast MEMORY_DRIFT_DETECTED (delta_x = +120px)")
    print("  [h] + Enter : Broadcast SELF_HEALING_COMPLETED (emerald node)")
    print("  [a] + Enter : Automated sequence (Drift now -> Heal in 3 seconds)")
    print("  [q] + Enter : Quit server")
    print("=" * 70)

    try:
        while True:
            cmd = input().strip().lower()
            if cmd == "d":
                broadcast_ws({"event": "MEMORY_DRIFT_DETECTED", "delta_x": 120})
            elif cmd == "h":
                broadcast_ws({"event": "SELF_HEALING_COMPLETED", "node_id": "submit", "color": "#10b981"})
            elif cmd == "a":
                broadcast_ws({"event": "MEMORY_DRIFT_DETECTED", "delta_x": 120})
                time.sleep(3)
                broadcast_ws({"event": "SELF_HEALING_COMPLETED", "node_id": "submit", "color": "#10b981"})
            elif cmd == "q":
                break
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        server.shutdown()
        print("[*] BE2 Server stopped.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
