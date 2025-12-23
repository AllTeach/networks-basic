# Session 1 — Simple Echo (Hands-On) + Exploring Networking Basics

Welcome! This page is for you to get hands-on experience with Python networking concepts. By the end of this session, you’ll:
- Run a minimal TCP echo server and a simple client.
- Learn about IP addresses, ports, and how TCP works at a basic level.
- Use tools like telnet/netcat to explore networking manually.
- Tackle 4 fun exercises that will deepen your understanding of stateful interactions and client-server communication.

---

## Why Learn Networking? (Introduction to TCP/IP Basics)
Before diving in, let’s understand **why** we’re learning this.

At the heart of most networking programs is the **OSI Model**, which splits communication into 7 layers. We focus on **Layer 4 (Transport Layer)**, which handles **TCP** (Transmission Control Protocol) and **UDP** (User Datagram Protocol). Here’s the key difference:

- **TCP**: Reliable, ensures all messages arrive in order (like Certified Mail or a phone call). We’ll use this for our exercises.
- **UDP**: Lightweight, faster, but unreliable (like Postcards or Radio Broadcasts).

By creating an Echo server today, you’ll see **how TCP's reliable connection works**, where devices exchange byte streams over virtual circuits.

---

## Networking Basics You Need to Know
### What is an IP Address?
Think of an **IP address** as the address of your computer on a network. It’s how devices locate each other and communicate.

- `127.0.0.1`: Known as "localhost," this refers to your own computer.
- `192.168.x.x` or `10.x.x.x`: Private network IPs, used for communication within a local network (e.g., at home or in class).
- `0.0.0.0`: Special IP that tells a server to accept connections on **all available interfaces** (localhost + any external network IP).

---

### What is a Port?
A **port** is like a "door" on your IP address where specific services (programs) listen for connections. Every networking app needs a unique port to differentiate itself.

- Common ports:
  - **Port 80**: HTTP (Web servers).
  - **Port 443**: HTTPS (Secure web traffic).
  - **Port 65432**: Our chosen port for demos today (random and above 1024 to avoid conflicts).

---

## 🛠 Task 0 — Confirm Your Environment is Ready
Before starting, ensure Python and network configurations are set up on your machine.

1. Run the script below to verify your IP address:
   ```python
   # Save this as sanity_check.py
   import socket
   print("Local IP address:", socket.gethostbyname(socket.gethostname()))
   ```
   - This confirms that Python’s `socket` library is working. The printed IP address (`192.168.x.x`, etc.) can be used for external device connections during exercises.
   
2. Check your Python version:
   ```bash
   python3 --version
   ```
   Ensure it’s **Python 3.8+**.

---

## Manual Exploration (Optional) — Using Telnet/Netcat
Understanding networking means knowing **how it works under the hood**.

1. Use `telnet` or `nc` to connect to a public website:
   ```bash
   telnet google.com 80
   ```
   Type:
   ```
   GET / HTTP/1.1
   ```

2. Observe the raw data returned. You’ve just simulated connecting directly to a web server!

This task helps you see that **networking is about simple text-based communication over sockets**, demystifying tools like Python `socket`.

---

## 🛠 Task 1 — Start with an Echo Server
Your first hands-on task is running a **minimal TCP echo server** and client. The server will listen for client messages and send them back unchanged.

Save the two files below to your working directory.

### Server Code: `echo_server.py`
```python
#!/usr/bin/env python3
import socket

HOST = "127.0.0.1"
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Listening on {HOST}:{PORT}")
    conn, addr = s.accept()
    with conn:
        print("Connected by", addr)
        while True:
            data = conn.recv(1024)
            if not data:
                print("Client closed connection")
                break
            conn.sendall(data)
```

### Client Code: `echo_client.py`
```python
#!/usr/bin/env python3
import socket

HOST = "127.0.0.1"
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Connected to server. Type your message (empty input to quit).")
    while True:
        message = input("> ")
        if not message:
            print("Goodbye!")
            break
        s.sendall(message.encode("utf-8"))
        data = s.recv(1024)
        print("Received:", data.decode("utf-8"))
```

### Steps:
1. Open a terminal and run `echo_server.py`.
2. Open another terminal and run `echo_client.py`.
3. Type messages in the client terminal and see the server echo them back.

---

## 🛠 Exercise 2 — Greeting Server
Goal: Extend the Echo server so it greets users by name.

**Protocol**:
1. Client sends its name (`John\n`).
2. Server replies: **Hello John!**
3. Server continues echoing any additional messages.

---

## 🛠 Exercise 3 — Number Ladder
Goal: Implement a game where the client and server take turns sending numbers until a target is reached.

**Protocol**:
1. Client sends its name and target integer `N`.
2. Server sends "1").
3. Client reads the number, increments it, and sends it back.
4. The sequence continues until one party sends `N`, followed by `DONE`.

---

## 🛠 Exercise 4 — Message Bridge
Goal: Relay messages between two clients using the server as a "bridge."

**Protocol**:
1. Server accepts Client A and Client B.
2. Messages are relayed:
   - A → Server → B as `From A: {message}`
   - B → Server → A as `From B: {message}`
3. If any client sends `EXIT`, both clients disconnect with a `DONE` message.

---

## Troubleshooting
- **Connection refused**: Ensure the server is running before starting the client.
- **Address already in use**: Restart the server or choose another port.
- **Mixed messages**: Ensure proper encoding/decoding in UTF-8.

---

Enjoy the exercises, and don’t hesitate to ask questions during the session!