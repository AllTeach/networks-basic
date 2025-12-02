#!/usr/bin/env python3
"""
Client for the greeting server.

Usage:
  python3 greeting_client.py

Behavior:
- Prompt for name, send it as first line, read greeting, then allow interactive sends (echo).
"""
import socket

HOST = "127.0.0.1"
PORT = 65433

def main():
    name = input("Your name: ").strip() or "Anon"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        # Send name
        s.sendall((name + "\n").encode("utf-8"))
        # Read greeting
        greeting = s.recv(4096)
        if not greeting:
            print("No greeting; server closed")
            return
        print("Server:", greeting.decode("utf-8", errors="replace").strip())
        # Interactive echo
        try:
            while True:
                line = input("> ")
                if not line:
                    print("Quitting")
                    break
                s.sendall((line + "\n").encode("utf-8"))
                data = s.recv(4096)
                if not data:
                    print("Server closed")
                    break
                print("Reply:", data.decode("utf-8", errors="replace").strip())
        except KeyboardInterrupt:
            print("\nClient exiting")

if __name__ == "__main__":
    main()