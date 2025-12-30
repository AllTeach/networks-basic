# Session 2 — Concurrency & Real-Time Chat (Minimal Student Codelab)

Goal (very short)
- See why single-threaded programs block.
- Make a client that receives messages while you type.
- Make a server that accepts multiple clients (one thread per client) and broadcasts messages.
- Keep everything minimal: no locks, no buffer management beyond readline(), just the simplest code that works for a classroom demo.

Important note (read this before running)
- These examples are intentionally minimal for learning. They omit locks and many production checks on purpose so you can see the core ideas clearly.
- Because there are no locks and little error handling, these examples are not safe for production or for extremely high load. They are for learning and lab practice only.

Prerequisites
- Python 3.8+ installed
- A terminal for each client (or terminal tabs)
- If you connect across machines: know the server machine's LAN IP and ensure network/firewall allows the port.

Quick start (do this now)
1. Save the server file below as `simple_server_no_locks.py`
2. Save the client file below as `simple_client_no_locks.py`
3. Run the server:
   - python3 simple_server_no_locks.py
4. Run the client in other terminals:
   - python3 simple_client_no_locks.py
   - If the server runs on another machine, edit the client's HOST at the top of the client file to the server IP.

What "minimal" means here
- Server uses a global list `clients = []` without any locking.
- Client and server use socket.makefile().readline() to read lines (simple framing: every message ends with '\n').
- No attempt to handle every possible network error — we keep the code short so the classroom can focus on threading and message flow.

---

## Minimal server (no locks)

Code (save as simple_server_no_locks.py)

```python
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
            # mark for removal; we won't modify the list while iterating in-place
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
```

Explanation (very short & clear)
- We use `socket.accept()` in the main thread.
- For every accepted connection we spawn a new thread running `handle_client`.
- `handle_client` uses `conn.makefile('r')` and `readline()` to get complete lines terminated by `\n` (this is simple framing).
- We store `(conn, name)` in `clients` so `broadcast()` can iterate and send messages.
- `broadcast` attempts to send and removes any sockets that raise errors.
- There are no locks and minimal error handling — this keeps the code short and readable for a lab.

Caveats (students must know)
- Removing entries from `clients` while other threads also iterate it can lead to race conditions. In practice this small example usually works for a short lab, but it's not robust. Later sessions will teach locks and safer patterns.

---

## Minimal client (no extra buffering)

Code (save as simple_client_no_locks.py)

```python
#!/usr/bin/env python3
# simple_client_no_locks.py -- minimal threaded client to receive while you type

import socket
import threading
import sys

HOST = '127.0.0.1'  # change to server IP if needed
PORT = 65433

def listener(sock):
    """Read lines from the socket and print them immediately."""
    f = sock.makefile('r', encoding='utf-8', newline='\n')
    try:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            print("\r" + line)
            print("> ", end='', flush=True)
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass
        sys.exit(0)

def main():
    name = input("Your name: ").strip() or "Anon"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    # send name as first line
    s.sendall((name + '\n').encode('utf-8'))

    # start listener thread
    t = threading.Thread(target=listener, args=(s,), daemon=True)
    t.start()

    print("Connected. Type messages and press Enter. Type EXIT to quit.")
    try:
        while True:
            line = input("> ")
            if not line:
                continue
            s.sendall((line + '\n').encode('utf-8'))
            if line.strip().upper() == 'EXIT':
                break
    except KeyboardInterrupt:
        pass
    finally:
        try:
            s.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()
```

Explanation (very short)
- The main thread prompts you for input and sends each line ending with `\n`.
- A listener thread uses `socket.makefile().readline()` (via the file iterator `for line in f`) to block for complete lines and print them as they arrive.
- The printing code attempts to preserve the prompt by printing the incoming line and then reprinting `> `.
- No locks, minimal cleanup.

---

## Very quick exercises (5–15 minutes each)

1) Simple group chat
- Run `simple_server_no_locks.py`.
- Run `simple_client_no_locks.py` in three terminals.
- Send messages, see them broadcast.

2) Exit/cleanup
- Type `EXIT` in a client; verify it closes and server announces leave.

3) Observe races (learning exercise)
- While two clients are sending messages rapidly and one client disconnects, watch the server output. Discuss why this minimal code can show odd behavior (race conditions). This motivates the need for locks in the next session.

---

## Short recap (students)
- This minimal setup demonstrates the essentials: blocking sockets, threads to allow concurrency, a simple newline framing protocol, and broadcasting messages.
- It's intentionally tiny so you see the core mechanics. Later sessions will reintroduce locks, buffering details, and production practices.

If you want this exact minimal version added to the repository (file names: `simple_server_no_locks.py`, `simple_client_no_locks.py`, and this markdown `session2_concurrency.md`), say "commit these files" and I will provide a patch you can apply or the git commands to add them.  