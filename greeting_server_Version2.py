#!/usr/bin/env python3
"""
Greeting server.

Protocol:
- Client connects and MUST send its name as the first newline-terminated line.
- Server replies with "Hello {name}!\n".
- Afterwards the server echoes any further lines from the client.

Usage:
  python3 greeting_server.py
"""
import socket

HOST = "127.0.0.1"
PORT = 65433  # different port from simple echo to allow side-by-side tests

def recv_line(conn):
    """Receive bytes until newline. Returns decoded str (without newline) or None if closed."""
    buf = b""
    while True:
        chunk = conn.recv(1024)
        if not chunk:
            return None
        buf += chunk
        if b"\n" in buf:
            line, rest = buf.split(b"\n", 1)
            # If there's extra (rest), we leave it in a simple per-connection buffer approach.
            return line.decode("utf-8", errors="replace").strip()

def handle_connection(conn, addr):
    print("Accepted", addr)
    # Receive name (first line)
    name = recv_line(conn)
    if name is None:
        print("No name received; closing")
        return
    print("Client name:", name)
    conn.sendall(f"Hello {name}!\n".encode("utf-8"))
    # Echo loop (line-based)
    # Simple approach: read raw bytes and echo them back as-is
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                print("Client disconnected:", name)
                break
            conn.sendall(data)
    except Exception as ex:
        print("Connection error:", ex)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Greeting server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                handle_connection(conn, addr)

if __name__ == "__main__":
    main()