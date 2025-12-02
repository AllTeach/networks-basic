#!/usr/bin/env python3
"""
Turn-based Message Bridge (single-threaded, blocking)

Behavior:
- Accept client A (first accept) and read its name (first newline-terminated line).
- Accept client B (second accept) and read its name.
- Tell A that it starts and tell B to wait.
- Loop:
    - Read one line from A, forward it to B prefixed "From {A}: ".
    - If A sent "EXIT", send "DONE" to both and close.
    - Read one line from B, forward it to A prefixed "From {B}: ".
    - If B sent "EXIT", send "DONE" to both and close.
- This is a strict alternation protocol. If a client does not follow the turn rules
  (e.g., sends when it's not their turn) the server may block or messages may be
  queued by the TCP stacks — this design is intentional to show a simple
  non-threaded relay that relies on clients following the protocol.
"""
import socket
from typing import Optional

HOST = "127.0.0.1"
PORT = 65435

def recv_line_blocking(conn: socket.socket) -> Optional[str]:
    """Read bytes from conn until newline. Return decoded line (without newline) or None on EOF."""
    buf = b""
    while True:
        chunk = conn.recv(1024)
        if not chunk:
            return None
        buf += chunk
        if b"\n" in buf:
            line, rest = buf.split(b"\n", 1)
            # note: we discard `rest` here — protocol expects tidy clients
            return line.decode("utf-8", errors="replace").strip()

def send_line(conn: socket.socket, text: str) -> bool:
    """Send text + newline. Return False on error, True otherwise."""
    try:
        conn.sendall((text + "\n").encode("utf-8"))
        return True
    except Exception:
        return False

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ls:
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.bind((HOST, PORT))
        ls.listen()
        print(f"Turn-bridge listening on {HOST}:{PORT}")
        print("Waiting for client A (first)...")
        conn_a, addr_a = ls.accept()
        print("A connected from", addr_a)
        with conn_a:
            name_a = recv_line_blocking(conn_a)
            if name_a is None:
                print("A disconnected before sending name")
                return
            print("A name:", name_a)
            # Accept B
            print("Waiting for client B (second)...")
            conn_b, addr_b = ls.accept()
            print("B connected from", addr_b)
            with conn_b:
                name_b = recv_line_blocking(conn_b)
                if name_b is None:
                    print("B disconnected before sending name")
                    return
                print("B name:", name_b)

                # Notify roles
                send_line(conn_a, f"ROLE:A You start. Send one line and press Enter.")
                send_line(conn_b, f"ROLE:B Wait for peer; you will send after you receive a line.")

                # Alternating relay loop
                while True:
                    # Read from A, forward to B
                    line_a = recv_line_blocking(conn_a)
                    if line_a is None:
                        # A disconnected unexpectedly -> notify B and exit
                        send_line(conn_b, f"NOTICE: Peer {name_a} disconnected")
                        print("A disconnected; closing bridge")
                        break
                    print(f"Received from A ({name_a}):", line_a)
                    if line_a == "EXIT":
                        # Inform both and close
                        send_line(conn_b, "DONE")
                        send_line(conn_a, "DONE")
                        print("EXIT received from A; shutting down")
                        break
                    send_line(conn_b, f"From {name_a}: {line_a}")

                    # Read from B, forward to A
                    line_b = recv_line_blocking(conn_b)
                    if line_b is None:
                        send_line(conn_a, f"NOTICE: Peer {name_b} disconnected")
                        print("B disconnected; closing bridge")
                        break
                    print(f"Received from B ({name_b}):", line_b)
                    if line_b == "EXIT":
                        send_line(conn_a, "DONE")
                        send_line(conn_b, "DONE")
                        print("EXIT received from B; shutting down")
                        break
                    send_line(conn_a, f"From {name_b}: {line_b}")

        print("Bridge closed. Goodbye.")

if __name__ == "__main__":
    main()