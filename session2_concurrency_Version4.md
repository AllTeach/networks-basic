# Session 2 — Concurrency & Real-Time Chat (Student Codelab)

What you'll learn
- Why single-threaded socket programs block and how that limits interactivity.
- How to make a client that can receive messages while you type.
- How to build a server that handles many clients at the same time (one thread per client).
- How to implement a simple broadcast chat room (everyone hears everyone).
- How to handle TCP stream framing (message boundaries) to avoid lost or merged messages.

Prerequisites
- Python 3.8+ installed on your computer.
- Basic knowledge from Session 1: you should have run the echo server and a simple client.
- A terminal (or terminal tab) for each client you will run.

Files you will use from the repository
- threaded_chat_client.py — a threaded client already in the repo. Use this as the client for the exercises.
  - Path: ./threaded_chat_client.py
- You will create/save one server file for this codelab: `simple_chat_server.py` (code included with this codelab).

Quick start (do this now)
1. Save the server file included with this codelab as `simple_chat_server.py`.
2. In one terminal run the server:
   - python3 simple_chat_server.py
3. In other terminals run the repository client:
   - python3 threaded_chat_client.py
   - If the server is on another machine, edit `threaded_chat_client.py` and set HOST to the server's IP (ask your instructor or check the server's LAN IP).

How this codelab is organized
1. See the blocking problem and why concurrency helps.
2. Learn client-side concurrency (what the threaded client does).
3. Build a thread-per-client server that broadcasts messages.
4. Understand TCP stream framing and how to buffer correctly.
5. Exercises and troubleshooting.

---

## 1 — The blocking problem (short)

What happens with a single-threaded client or server?
- `recv()`, `accept()` and `input()` are blocking calls: they stop the current thread until data or input arrives.
- If a program uses one thread for everything, it cannot both wait for keyboard input and also process incoming network data at the same time.
- The turn-based example from Session 1 (strict alternation) intentionally blocks; it is useful for learning protocols, but not for free-form chat.

Why fix it?
- For a chat application you want to see incoming messages while you type. That requires concurrency.

---

## 2 — Client-side concurrency (what your repo client does)

Goal
- The client should be able to receive messages and print them immediately while you still have the input prompt open.

How it works (concept)
- The client spawns a background thread that loops on `recv()` and prints messages as they arrive.
- The main thread loops on `input()` and sends what you type.
- Because `recv()` runs in its own thread, incoming messages do not block your ability to type.

What you will do
- Run the existing `threaded_chat_client.py` from the repository.
- If you want, open it and inspect how it receives data in a separate thread.

Notes for the client in the repo
- The repo's `threaded_chat_client.py` uses `recv(1024)` in the listener thread and prints messages directly.
- If the server sends newline-delimited messages, this client works for interactive chat; if messages are large or many come quickly, add buffering (see framing section).

---

## 3 — Server-side concurrency: a thread per client

Goal
- Make a server that accepts any number of clients and spawns a handler thread for each connection. Each handler can block on `recv()` without blocking the server from accepting other clients.

Save the following as `simple_chat_server.py` and run it:

```python
#!/usr/bin/env python3
# simple_chat_server.py
# Thread-per-client broadcast chat server (newline-delimited)

import socket
import threading

HOST = '0.0.0.0'   # listen on all interfaces (useful in LAN/classroom)
PORT = 65433       # matches threaded_chat_client.py in repo

clients = []  # list of tuples (conn, name)
clients_lock = threading.Lock()

def send_line(conn, text):
    try:
        conn.sendall(text.encode('utf-8') + b'\n')
        return True
    except Exception:
        return False

def broadcast(text, exclude_conn=None):
    with clients_lock:
        for conn, _ in clients[:]:
            if conn is exclude_conn:
                continue
            ok = send_line(conn, text)
            if not ok:
                remove_client(conn)

def remove_client(conn):
    with clients_lock:
        for entry in clients[:]:
            if entry[0] is conn:
                clients.remove(entry)
                try:
                    conn.close()
                except Exception:
                    pass
                break

def recv_lines(conn, buffer):
    """
    Read bytes from conn, append to buffer, return complete lines (no newline).
    Returns (lines, buffer). If recv() returns empty (EOF) returns (None, buffer).
    """
    try:
        data = conn.recv(1024)
    except Exception:
        return None, buffer
    if not data:
        return None, buffer
    buffer.extend(data)
    lines = []
    while b'\n' in buffer:
        idx = buffer.index(b'\n')
        raw = bytes(buffer[:idx])
        line = raw.decode('utf-8', errors='replace').rstrip('\r')
        lines.append(line)
        del buffer[:idx+1]
    return lines, buffer

def handle_client(conn, addr):
    buffer = bytearray()
    # Read nickname as first line
    lines, buffer = recv_lines(conn, buffer)
    if lines is None:
        conn.close()
        return
    while lines == []:
        lines, buffer = recv_lines(conn, buffer)
        if lines is None:
            conn.close()
            return
    name = lines[0].strip() or f"{addr}"
    with clients_lock:
        clients.append((conn, name))
    print(f"{name} joined from {addr}")
    broadcast(f"SERVER: {name} has joined the chat.", exclude_conn=conn)
    try:
        while True:
            lines, buffer = recv_lines(conn, buffer)
            if lines is None:
                # Client disconnected
                break
            for line in lines:
                if line.strip().upper() == 'EXIT':
                    send_line(conn, "DONE")
                    break
                text = f"{name}: {line}"
                print(text)          # server-side log
                broadcast(text, exclude_conn=conn)
            else:
                continue
            break
    finally:
        remove_client(conn)
        broadcast(f"SERVER: {name} has left the chat.", exclude_conn=None)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ls:
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.bind((HOST, PORT))
        ls.listen()
        print(f"Chat server listening on {HOST}:{PORT}")
        while True:
            conn, addr = ls.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

if __name__ == '__main__':
    main()
```

Student-friendly explanation
- The first line a client sends is considered the client's nickname.
- Each client handler keeps its own `bytearray()` buffer. This buffer is used to collect bytes from `recv()` and extract complete lines ending with `\n`.
- `broadcast()` sends a text line to all currently connected clients except the sender. It removes any client that fails to receive.
- All manipulations to `clients` happen under `clients_lock` to avoid concurrent access problems.

Try this now
1. In one terminal run the server:
   - python3 simple_chat_server.py
2. In other terminals run the repository client:
   - python3 threaded_chat_client.py
3. Enter a nickname (if client prompts) and send messages. Everyone connected should see each other's messages.

---

## 4 — TCP is a stream: framing and buffering

Important concept
- TCP is a continuous stream of bytes. It does not preserve the boundaries of the `send()` calls.
- The result: two short messages sent quickly may arrive combined in a single recv(). A large message may be split across multiple recv() calls.

How we avoid mistakes
- Use a framing protocol. For this codelab we use a newline (`\n`) delimiter: every message ends with `\n`.
- On receive, keep leftover bytes in a per-connection buffer and only process complete lines.

Buffering pattern (concept)
```python
buffer = bytearray()
data = conn.recv(1024)
buffer.extend(data)
while b'\n' in buffer:
    idx = buffer.index(b'\n')
    line = bytes(buffer[:idx]).decode('utf-8', errors='replace')
    process(line)
    del buffer[:idx+1]
```

Advanced option (homework)
- Use length-prefixed framing (4-byte big-endian length header):
  - Sender: send 4-byte length + message bytes.
  - Receiver: read exactly 4 bytes, parse length, then read that many bytes.
- This option is binary-safe and avoids delimiter-escaping issues.

---

## 5 — Tasks (do these during the session)

Task 1 — Connect and chat (5–10 minutes)
- Run the server and connect multiple clients using the repo's `threaded_chat_client.py`.
- Exchange messages and observe how messages appear while you type.

Task 2 — Inspect and explain (10–15 minutes)
- Open `threaded_chat_client.py` and find the listener thread. Explain in one sentence how it allows receiving and typing concurrently.
- Open `simple_chat_server.py` (saved locally) and find `recv_lines()`. Explain how it avoids message-boundary bugs.

Task 3 — Add `/name` command (20–30 minutes)
- Modify `threaded_chat_client.py` so you can type `/name <newname>` to change your displayed nickname (the client should send this to the server; server should update the name).
- On the server: accept the name change and broadcast a "SERVER: <old> is now <new>" message.

Task 4 — Robust removal of dead clients (15 minutes)
- On the server, try to intentionally crash one client (close its terminal). Confirm the server removes the dead socket from the `clients` list and continues working.

Task 5 (optional homework) — Length-prefixed framing
- Implement the length-prefix protocol on both client and server using `struct.pack('!I', len(msg))` and `struct.unpack('!I', header)`.
- Verify that the framing still works for very large messages and binary payloads.

---

## 6 — Troubleshooting (common issues & fixes)

- Connection refused:
  - Ensure the server is running and the port matches in the client.
  - If connecting across machines, ensure firewall allows the port and the server host IP is reachable.
- Address already in use:
  - A previous server process may be still bound to the port. Kill it or pick another port.
- Messages not displayed until Enter:
  - Check that the client you run is the threaded client with a listener thread. Single-threaded, turn-taking clients intentionally block until it is their turn.
- Mixed/merged messages:
  - That indicates missing buffering logic. Use per-connection buffers and split on `\n` as shown above.

Practical tips
- Use `HOST = '0.0.0.0'` on the server to accept LAN connections; use `HOST = '127.0.0.1'` on the client to connect locally.
- If you run client and server on different machines, change `HOST` in `threaded_chat_client.py` to the server machine IP (ask your instructor for the IP).
- If a client hangs on exit, press Ctrl+C to terminate and the server will clean up the dead client on the next broadcast attempt.

---

## 7 — What you learned and next steps

Today you practiced:
- Adding concurrency to clients and servers using threads.
- Building a broadcast chat server that handles many clients.
- Buffering and splitting a TCP stream by delimiter to avoid lost or combined messages.

Next topics you can explore (recommended)
- Non-blocking and asynchronous I/O (asyncio) — scales better than one-thread-per-client.
- Select/poll/epoll and worker thread pools.
- Transport security (TLS) to encrypt chat messages.
- Implementing persistent rooms, message history, and private messaging.

Happy coding — open terminals, connect multiple clients, and try a group chat!