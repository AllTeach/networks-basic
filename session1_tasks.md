# Session 1 — Simple Echo (hands-on) + 4 short exercises

Hello students — this page is for you. Follow the steps below to get hands-on quickly: run a minimal TCP echo server and a simple client, then try four short exercises to explore name exchange, stateful interactions, and relaying messages between clients.

---

## New: Why Are We Doing This? (The OSI Model & How It Connects Here)
Before diving into the code, spend 5 minutes understanding **why** we need networking protocols.
- **Networking happens at OSI Layer 4 (Transport Layer)**, where protocols like **TCP** and **UDP** live.
  - **TCP**: Reliable, like Certified Mail (e.g., your Python Echo server).
  - **UDP**: Unreliable but fast, like sending a postcard or radio broadcast.
  
By building an Echo server today, you'll see the basics of **TCP connections** and understand how low-level data forms the backbone of every internet interaction.

---

## New: Networking Basics – IP Addresses and Ports
Before jumping into Python socket programming, let's quickly define two core concepts:

1. **IP Address**:
   - The **IP address** is like the address of your computer on a network (local or global). It's how devices locate each other to exchange data.
   - Example IP addresses:
     - `127.0.0.1`: The "localhost" address means **this computer only**.
     - `192.168.x.x` or `10.x.x.x`: Private network IPs. You'll likely use one of these for home or classroom networks.
     - `0.0.0.0`: A special IP a server binds to if it wants to accept connections on **all available network interfaces** (e.g., localhost + external IPs).

2. **Port**:
   - Think of a **port** as a "door" in your IP address where specific applications or services listen for connections.
   - Every networking program uses a unique port to differentiate itself. For example:
     - **Port 80**: Commonly used for HTTP (websites).
     - **Port 65432 (our Echo server)**: A randomly chosen port number for our custom application.
   - Ports under 1024 are "privileged" and typically require admin access to bind.

In today’s exercises:
- You'll use `127.0.0.1` for IP (loopback for your machine).
- Each program runs on a **unique port** to avoid conflicts.

---

## 🛠 Task 0 — Sanity Check: Is Your Setup Ready?
Before starting, ensure your environment is ready.
1. Run the following code snippet to check Python and networking setup:

```python
# Save this as sanity_check.py
import socket
print("Finding your local IP address...")
print("Local IP address:", socket.gethostbyname(socket.gethostname()))
```

2. Expected Output:
   - This script prints your **local IP address**, confirming that Python and networking configurations work. Use this IP for connections outside `127.0.0.1` (localhost).

---

## Prerequisites
- Python 3.8+ installed (check with: `python3 --version`)
- A terminal or command prompt
- Recommended: Open two or three terminal windows (server + one or two clients)

---

## Quick Overview
- **Files you will use in this session:**
  - `echo_server.py` (minimal echo server)
  - `echo_client.py` (minimal interactive client)
  - `greeting_server.py` / `greeting_client.py` (optional demo)
  - `number_ladder_server.py` / `number_ladder_client.py` (exercise)
  - `bridge_server.py` / `simple_bridge_client.py` (exercise)

- **Ports used (all on 127.0.0.1 / localhost):**
  - Echo: **65432**
  - Greeting: **65433**
  - Number Ladder: **65434**
  - Message Bridge: **65435**

---

## A. Starter: Minimal Echo Server & Client (Do This First)
- Save the two files below as `echo_server.py` and `echo_client.py` and run them.

```python name=echo_server.py
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

```python name=echo_client.py
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

---

## New: How It Works (Short Explanation)
### Before You Start, Understand These Concepts:
1. `socket(socket.AF_INET, socket.SOCK_STREAM)`: Creates an IPv4 TCP socket.
2. `bind((HOST, PORT))`: Server reserves `IP:port` for listening.
3. `listen(backlog)`: Marks the socket to accept incoming connections.
4. `accept()`: Blocks until a client connects; returns `(conn, addr)`. Use `conn` to communicate with that client.
5. `recv(bufsize)`: Reads up to `bufsize` bytes (remember that data may arrive in chunks).
6. `sendall(data)`: Sends all bytes in `data`.
7. `connect((HOST, PORT))`: Client connects to the server (performs a TCP handshake).

Remember: **TCP is a byte stream**, so use `str.encode()` for sending and `str.decode()` for receiving.

---

## B. Manual Exploration with Telnet/Netcat (Optional Precursor) ...
[Content continues as outlined above.]