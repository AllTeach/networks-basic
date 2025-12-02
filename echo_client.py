#!/usr/bin/env python3
"""
Simple interactive TCP echo client.

Usage:
  python3 echo_client.py

Behavior:
- Connects to 127.0.0.1:65432 by default.
- Reads lines from stdin, sends them to server, prints server reply.
- Empty line quits.
"""
import socket

HOST = "127.0.0.1"
PORT = 65432

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}. Type lines (empty line to quit).")
        try:
            while True:
                line = input("> ")
                if line == "":
                    continue
                s.sendall((line + "\n").encode())
        except (KeyboardInterrupt, EOFError):
            print("\nExiting")
            try:
                s.close()
            except Exception:
                pass
            sys.exit(0)

if __name__ == "__main__":
    main()
