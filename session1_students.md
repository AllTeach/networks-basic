# Session 1 — Student Lab Notebook (Hands-on first, then theory)

## Quick note
This file includes the complete code for the session (so you can view/copy directly) and the lab steps below. The same Python files will also be uploaded individually in the repository so you can run them directly.

---

## Code snippets (copy these into files or use the provided files)

### echo_server.py
```python
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
```

### echo_client.py
```python
#!/usr/bin/env python3
"""
Simple TCP echo client.
Run: python3 echo_client.py
"""
import socket

HOST = "127.0.0.1"
PORT = 65432

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        try:
            while True:
                text = input("Send (empty to quit): ")
                if not text:
                    break
                s.sendall(text.encode("utf-8"))
                data = s.recv(4096)
                if not data:
                    print("Server closed connection")
                    break
                print("Received:", data.decode("utf-8", errors="replace"))
        except KeyboardInterrupt:
            print("\nClient exiting")

if __name__ == "__main__":
    main()
```

### selectors_broadcast_server.py
```python
#!/usr/bin/env python3
"""
Selector-based, non-blocking broadcast/chat server (newline-delimited).
Run: python3 selectors_broadcast_server.py
Clients should be chat_client.py (provided).
"""
import selectors
import socket
import types

HOST = "127.0.0.1"
PORT = 65435

sel = selectors.DefaultSelector()
clients = {}  # socket -> data namespace with addr, inb, outb, name

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print("Accepted", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", name=None)
    clients[conn] = data
    sel.register(conn, selectors.EVENT_READ, data=data)
    # Ask for name
    data.outb += b"Welcome! Enter your name:\n"
    sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        try:
            recv = sock.recv(4096)
        except ConnectionResetError:
            recv = b""
        if recv:
            data.inb += recv
            # process newline-delimited messages
            while b'\n' in data.inb:
                line, rest = data.inb.split(b'\n', 1)
                data.inb = rest
                text = line.decode('utf-8', errors='replace').strip()
                if not data.name:
                    # first line is the username
                    data.name = text or f"{data.addr}"
                    welcome = f"Hello {data.name}! You can chat now.\n"
                    data.outb += welcome.encode()
                    broadcast(f"{data.name} has joined the chat.\n", exclude=sock)
                else:
                    broadcast(f"{data.name}: {text}\n", exclude=None)
            # ensure we are monitoring WRITE if we have outb
            if data.outb:
                sel.modify(sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)
        else:
            disconnect(sock)
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            try:
                sent = sock.send(data.outb)
            except BlockingIOError:
                sent = 0
            data.outb = data.outb[sent:]
        if not data.outb:
            try:
                sel.modify(sock, selectors.EVENT_READ, data=data)
            except Exception:
                # socket may have been unregistered during disconnect
                pass

def broadcast(message, exclude=None):
    bmsg = message.encode()
    to_remove = []
    for s, d in list(clients.items()):
        if s is exclude:
            continue
        d.outb += bmsg
        try:
            sel.modify(s, selectors.EVENT_READ | selectors.EVENT_WRITE, data=d)
        except Exception:
            to_remove.append(s)
    for s in to_remove:
        disconnect(s)

def disconnect(sock):
    d = clients.get(sock)
    if not d:
        return
    name = d.name or str(d.addr)
    print(f"Disconnecting {name}")
    try:
        sel.unregister(sock)
    except Exception:
        pass
    try:
        sock.close()
    except Exception:
        pass
    del clients[sock]
    broadcast(f"{name} has left the chat.\n", exclude=None)

def main():
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print(f"Selector broadcast server listening on {(HOST, PORT)}")
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Shutting down")
    finally:
        sel.close()

if __name__ == "__main__":
    main()
```

### chat_client.py
```python
#!/usr/bin/env python3
"""
Simple chat client that reads incoming messages in a background thread.
Run: python3 chat_client.py
"""
import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 65435

def recv_loop(s):
    try:
        while True:
            data = s.recv(4096)
            if not data:
                print("\nConnection closed by server")
                break
            print("\n" + data.decode("utf-8", errors="replace"), end="")
            print("> ", end="", flush=True)
    except Exception:
        pass

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        t = threading.Thread(target=recv_loop, args=(s,), daemon=True)
        t.start()
        try:
            while True:
                line = input("> ")
                if not line:
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
```

### threaded_broadcast_server.py
```python
#!/usr/bin/env python3
"""
Thread-per-connection broadcast/chat server.
Run: python3 threaded_broadcast_server.py
Clients: chat_client.py
"""
import socket
import threading

HOST = "127.0.0.1"
PORT = 65436

clients_lock = threading.Lock()
clients = {}  # conn -> name

def broadcast(message, exclude_conn=None):
    with clients_lock:
        to_remove = []
        for conn in list(clients.keys()):
            if conn is exclude_conn:
                continue
            try:
                conn.sendall(message.encode())
            except Exception:
                to_remove.append(conn)
        for conn in to_remove:
            remove_client(conn)

def remove_client(conn):
    with clients_lock:
        name = clients.pop(conn, None)
    try:
        conn.close()
    except Exception:
        pass
    if name:
        broadcast(f"{name} has left the chat.\n")

def handle_client(conn, addr):
    with conn:
        conn.sendall(b"Welcome! Enter your name:\n")
        try:
            data = b""
            # read username line
            while b"\n" not in data:
                chunk = conn.recv(1024)
                if not chunk:
                    return
                data += chunk
            name = data.split(b"\n", 1)[0].decode().strip() or f"{addr}"
            with clients_lock:
                clients[conn] = name
            conn.sendall(f"Hello {name}! You can chat now.\n".encode())
            broadcast(f"{name} has joined the chat.\n", exclude_conn=conn)
            # Now handle messages
            rest = data.split(b"\n", 1)[1] if b"\n" in data else b""
            while True:
                if rest:
                    line, _, rest = rest.partition(b"\n")
                    text = line.decode(errors="replace").strip()
                    broadcast(f"{name}: {text}\n", exclude_conn=None)
                else:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    rest += chunk
        except Exception:
            pass
    remove_client(conn)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Threaded broadcast server listening on {(HOST, PORT)}")
        try:
            while True:
                conn, addr = s.accept()
                t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                t.start()
        except KeyboardInterrupt:
            print("Shutting down")

if __name__ == "__main__":
    main()
```