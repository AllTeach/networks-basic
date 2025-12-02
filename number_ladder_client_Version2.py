#!/usr/bin/env python3
"""
Client for Number Ladder.

Usage:
  python3 number_ladder_client.py

Behavior:
- Prompt for name and target N.
- Send name and N to server (newline-terminated).
- Then alternate: receive number, print, increment and send back.
- When server sends DONE, client exits.
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
            return line.decode("utf-8", errors="replace").strip()

def main():
    name = input("Your name: ").strip() or "Anon"
    try:
        target = int(input("Target N (positive integer): ").strip())
    except Exception:
        print("Invalid target")
        return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall((name + "\n").encode("utf-8"))
        s.sendall((str(target) + "\n").encode("utf-8"))
        while True:
            line = recv_line(s)
            if line is None:
                print("Server closed")
                break
            if line == "DONE":
                print("Server: DONE. Finished.")
                break
            print("Server sent:", line)
            try:
                num = int(line.strip())
            except Exception:
                print("Received non-number:", line)
                break
            # Increment and send back
            to_send = str(num + 1) + "\n"
            s.sendall(to_send.encode("utf-8"))

if __name__ == "__main__":
    main()