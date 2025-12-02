#!/usr/bin/env python3
"""
Blocking TCP echo server (single client handling loop).
Run: python3 echo_server.py
"""
import socket

HOST = "127.0.0.1"
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Listening on {(HOST, PORT)}")
    conn, addr = s.accept()
    with conn:
        print("Connected by", addr)
        while True:
            data = conn.recv(1024)
            if not data:
                print("Client disconnected")
                break
            # Echo back exactly what we got
            conn.sendall(data)