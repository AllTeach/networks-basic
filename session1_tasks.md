# Session 1 — Simple Echo (hands-on) + 4 short exercises

Hello students — this page is for you. Follow the steps below to get hands-on quickly: run a minimal TCP echo server and a simple client, then try four short exercises to explore name exchange, stateful message flow, and relaying between two clients. No formal submissions — just try the exercises, experiment, and ask questions in class.

Prerequisites
- Python 3.8+ installed (check with: python3 --version)
- A terminal or command prompt
- Recommended: open two or three terminal windows (server + one or two clients)

Quick overview
- Files you will use in this session:
  - echo_server.py        (minimal echo server)
  - echo_client.py        (minimal interactive client)
  - greeting_server.py / greeting_client.py (optional demo)
  - number_ladder_server.py / number_ladder_client.py (exercise)
  - bridge_server.py / simple_bridge_client.py (exercise)
- Ports used (all on 127.0.0.1 / localhost):
  - echo: 65432
  - greeting: 65433
  - number ladder: 65434
  - message bridge: 65435

A. Starter: Minimal Echo server & client (do this first)
- Save the two files below as `echo_server.py` and `echo_client.py` and run them.

echo_server.py
```python
#!/usr/bin/env python3
# Minimal blocking TCP echo server (single client at a time)
import socket

HOST = "127.0.0.1"   # local only
PORT = 65432         # free port >1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Listening on {HOST}:{PORT}")
    conn, addr = s.accept()
    with conn:
        print("Connected by", addr)
        while True:
            data = conn.recv(4096)
            if not data:
                print("Client closed")
                break
            conn.sendall(data)
```

echo_client.py
```python
#!/usr/bin/env python3
# Minimal interactive TCP echo client
import socket

HOST = "127.0.0.1"
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"Connected to {HOST}:{PORT}. Type lines (empty to quit).")
    try:
        while True:
            line = input("> ")
            if line == "":
                print("Quitting.")
                break
            s.sendall((line + "\n").encode("utf-8"))
            data = s.recv(4096)
            if not data:
                print("Server closed connection")
                break
            print("Echo:", data.decode("utf-8", errors="replace").rstrip("\n"))
    except KeyboardInterrupt:
        print("\nClient exiting")
```

B. Short explanation (read after you run the starter)
- socket.socket(AF_INET, SOCK_STREAM): create an IPv4 TCP socket.
- bind((HOST, PORT)): server reserves IP:port so clients can connect.
- listen(backlog): mark socket to accept incoming connections.
- accept(): block until a client connects; returns (conn, addr). Use conn to talk to that client.
- recv(bufsize): read up to bufsize bytes (may return less).
- sendall(data): send all bytes (blocks until done).
- connect((HOST, PORT)): client connects to server (TCP handshake).
- Encoding: send bytes, so call .encode("utf-8") before send; decode after recv().

C. Exercise 1 — Quick theory & short research (do this quickly)
For each of the following, write a 1–3 sentence answer. If you want, look up the Python socket docs or a short tutorial to confirm.
1. What does 0.0.0.0 mean when a server binds to it? How is that different from 127.0.0.1?
2. What does bind() do? Why do servers call it?
3. What does listen() do and what is backlog roughly?
4. What exactly does accept() return and why use that returned socket?
5. If recv() returns b'' what does it usually mean and how should your code react?
6. Why is it important to close sockets?
7. Why must the client call connect() before sendall() with TCP?
8. Why should you not assume recv() always returns a complete logical message? How can you handle partial reads?

Hints: check the Python docs (https://docs.python.org/3/library/socket.html) or a short tutorial if you need.

D. Exercise 2 — Greeting server (hands-on)
Goal: have a server that reads your name on connect and replies with "Hello {name}!"

- Protocol (simple):
  1. Client connects and sends its name as the first newline-terminated line.
  2. Server reads the name and replies exactly: Hello {name}!
  3. Afterwards the server echoes any lines the client sends.

Quick steps:
- Use the previously provided greeting_server.py and greeting_client.py if available, or modify the echo server/client to:
  - client: send name first (name + "\n")
  - server: read first line, send greeting, then echo.

Try it:
1. Run greeting server (port 65433).
2. Run greeting client, enter your name when prompted.
3. Observe the greeting from the server.

Optional: add a STATS command — if you send STATS the server returns how many messages you sent during the session.

E. Exercise 3 — Number Ladder (stateful number exchange)
Goal: practice stateful alternation of messages between client and server.

Protocol summary (simple classroom version):
1. Client sends name (first line).
2. Client sends an integer N (next line) as the target.
3. Server sends "1\n" to start.
4. Client reads a number, prints it, increments and sends the next; server reads it and sends the next, alternating.
5. When N is reached, the party that hits N sends "DONE\n" and connection closes.

Deliverable
- Run a session with N=5 and submit a transcript that shows the counting and `DONE`.

Hints
- Keep messages newline-terminated and parse per-line on both sides.
- Use int() conversions with try/except to handle bad input.

F. Exercise 4 — Message Bridge (two-client relay)
Goal: connect two clients A and B and forward lines between them.

Behavior:
- Server accepts client A, reads name A.
- Server accepts client B, reads name B.
- After both connected:
  - A → server → B as `From {A}: {line}`
  - B → server → A as `From {B}: {line}`
- If either client sends `EXIT`, the server sends `DONE` to both clients and closes both connections.
- If a client disconnects unexpectedly, server notifies the other and closes.

Try it:
1. Run bridge server (port 65435).
2. Run two instances of simple_bridge_client.py (or netcat).
3. Exchange messages; type EXIT to terminate the session.


G. Troubleshooting & tips
- If you get ConnectionRefusedError: check the server is running and you are connecting to the correct host/port.
- If "Address already in use": stop the previous server or pick another port.
- If you see garbled characters: check you consistently use UTF-8 encode/decode.
- Remember: TCP is a byte stream. If messages seem joined or split, implement simple newline-based framing and read into a buffer until you see '\n'.

H. Optional next steps (if you have time)
- Add length-prefixed framing instead of newline-delimited lines.

Enjoy the lab — try each exercise, play with the code, and ask questions during the session.
