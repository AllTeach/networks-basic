#!/usr/bin/env python3
"""
Simple turn-taking client for the turn-based bridge.

Usage:
  python3 turn_client.py

Behavior:
- Prompt for your name, connect to bridge server, send name (newline-terminated).
- Read initial ROLE message from server:
    - If ROLE:A -> you start (you send first).
    - If ROLE:B -> wait for peer's line, then you send.
- After sending a line you will wait to receive the peer's line.
- Send "EXIT" to terminate (server will forward DONE to both).
Notes:
- This client follows the strict alternation expected by the server. If you type
  while it's not your turn the server will not read it until it becomes your turn.
"""
import socket
import sys

HOST = "127.0.0.1"
PORT = 65435

def recv_line(conn: socket.socket):
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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        # Send name
        s.sendall((name + "\n").encode("utf-8"))

        # Read initial role/info line(s) from server
        initial = recv_line(s)
        if initial is None:
            print("Server closed")
            return
        print("Server:", initial)
        is_turn = initial.startswith("ROLE:A")

        try:
            while True:
                if is_turn:
                    # It's our turn to send
                    line = input("> ")
                    if line == "":
                        print("Empty line ignored. Type EXIT to leave.")
                        continue
                    s.sendall((line + "\n").encode("utf-8"))
                    if line == "EXIT":
                        # Server will send DONE to both; we'll read it and exit
                        resp = recv_line(s)
                        if resp is None:
                            print("Server closed")
                            break
                        print("Server:", resp)
                        break
                    # After sending, wait for peer's message
                    resp = recv_line(s)
                    if resp is None:
                        print("Server/peer closed")
                        break
                    print(resp)
                    # Next iteration peer will send, so we are not turn now
                    is_turn = False
                else:
                    # Wait for peer to send
                    resp = recv_line(s)
                    if resp is None:
                        print("Server/peer closed")
                        break
                    print(resp)
                    if resp == "DONE":
                        print("Session ended by peer.")
                        break
                    # Now it's our turn to send
                    is_turn = True
        except KeyboardInterrupt:
            print("\nInterrupted; exiting")
        finally:
            try:
                s.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()