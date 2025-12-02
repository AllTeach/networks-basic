#!/usr/bin/env python3
"""
Number Ladder server (replacement for ping-pong).

Protocol:
1) Client connects and sends its name as the first newline-terminated line.
2) Client sends integer N (newline-terminated) as the target.
3) Server sends "1\n" to the client to start.
4) Client and server alternate sending incrementing numbers as text lines.
   - If the party that receives N recognizes target reached, they reply/send "DONE\n" and close.
Notes:
- Single-client blocking server for simplicity.
"""
import socket

HOST = "127.0.0.1"
PORT = 65434

def recv_line(conn):
    buf = b""
    while True:
        chunk = conn.recv(1024)
        if not chunk:
            return None
        buf += chunk
        if b"\n" in buf:
            line, rest = buf.split(b"\n", 1)
            # Note: rest is discarded for simplicity (server expects tidy client behavior)
            return line.decode("utf-8", errors="replace").strip()

def handle_connection(conn, addr):
    print("Accepted", addr)
    name = recv_line(conn)
    if name is None:
        print("No name; closing")
        return
    target_line = recv_line(conn)
    if target_line is None:
        print("No target; closing")
        return
    try:
        target = int(target_line.strip())
    except Exception:
        conn.sendall(b"ERROR: invalid target\n")
        return
    print(f"{name} requested ladder up to {target}")
    # Server initiates
    current = 1
    try:
        while True:
            # Send current
            conn.sendall(f"{current}\n".encode("utf-8"))
            if current >= target:
                conn.sendall(b"DONE\n")
                print("Reached target; closing")
                break
            # Wait for client's increment
            line = recv_line(conn)
            if line is None:
                print("Client disconnected early")
                break
            try:
                val = int(line.strip())
            except Exception:
                conn.sendall(b"ERROR: invalid number\n")
                break
            # Server expects client's number to be current+1
            current = val + 1  # prepare next to send
            # Loop continues; next iteration server sends current
    except Exception as ex:
        print("Error during ladder:", ex)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Number Ladder server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                handle_connection(conn, addr)

if __name__ == "__main__":
    main()