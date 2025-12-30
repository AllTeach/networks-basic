#!/usr/bin/env python3
# simple_server_no_locks.py -- minimal thread-per-client broadcast server (no locks)

import socket
import threading

HOST = '0.0.0.0'   # listen on all interfaces (change to '127.0.0.1' to restrict)
PORT = 65433

clients = []  # list of (conn, name) tuples

def broadcast(text, except_conn=None):
    """Send a line (with newline) to all clients except except_conn."""
    to_remove = []
    for conn, _ in clients:
        if conn is except_conn:
            continue
        try:
            conn.sendall((text + '\n').encode('utf-8'))
        except Exception:
            to_remove.append(conn)
    # remove dead sockets after iterating
    for conn in to_remove:
        for entry in clients[:]:
            if entry[0] is conn:
                clients.remove(entry)

def handle_client(conn, addr):
    """Runs in a thread per client. Very simple: read name, then broadcast lines."""
    f = conn.makefile('r', encoding='utf-8', newline='\n')
    try:
        name = f.readline()
        if not name:
            conn.close()
            return
        name = name.strip() or f"{addr}"
        clients.append((conn, name))
        print(f"{name} joined from {addr}")
        broadcast(f"SERVER: {name} joined", except_conn=conn)

        for line in f:  # readline() loop: each iteration returns a line ending with '\n'
            line = line.rstrip('\n').rstrip('\r')
            if line.upper() == 'EXIT':
                try:
                    conn.sendall(b'DONE\n')
                except Exception:
                    pass
                break
            message = f"{name}: {line}"
            print(message)  # server log
            broadcast(message, except_conn=conn)
    finally:
        # cleanup (best-effort)
        for entry in clients[:]:
            if entry[0] is conn:
                clients.remove(entry)
        try:
            conn.close()
        except Exception:
            pass
        print(f"{name} @ {addr} left")
        broadcast(f"SERVER: {name} left")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Minimal chat server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

if __name__ == '__main__':
    main()