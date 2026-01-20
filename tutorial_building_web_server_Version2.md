# Tutorial — Building a Web Server from Scratch
Target audience: 11th Grade Gifted Engineering Students  
Prerequisite: Completion of the TCP/UDP Socket Lab

---

## Part 1 — The Concept

TCP (Transmission Control Protocol) is like a phone call: it gives you a reliable, ordered stream of bytes. HTTP (Hypertext Transfer Protocol) is an application‑level protocol that runs on top of TCP and expects that reliability.

Why TCP for web pages?  
If you tried to send an HTML page over UDP and a packet was lost or reordered, the browser could receive broken markup (e.g., pieces of `<h1>Hello</h1>` arriving out of order) and render nothing or garbage. Browsers (Chrome, Edge, Safari…) are TCP clients: they expect a continuous, ordered text stream.

In this exercise you will not use a web framework (Flask, Django). You will build a raw TCP server that speaks HTTP.

---

## Part 2 — The Implementation

Create a file named `http_server.py`. We'll reuse the TCP receive logic from the socket lab and adapt it to parse a simple HTTP request and send a valid HTTP response.

Code (save as `http_server.py`):

```python
#!/usr/bin/env python3
# http_server.py -- minimal HTTP server using raw TCP sockets

import socket

# 1. Initialize the socket (TCP)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 2. Bind to 0.0.0.0 so we listen on all interfaces (localhost, Wi‑Fi, Ethernet)
server_socket.bind(('0.0.0.0', 8080))

# 3. Start listening (backlog 1 is fine for this demo)
server_socket.listen(1)
print("Server is listening on port 8080...")

while True:
    # 4. Accept the incoming connection ("phone call")
    client_socket, client_address = server_socket.accept()
    print(f"Connection from: {client_address}")

    # 5. Receive the HTTP request (read up to 1024 bytes for demo)
    request = client_socket.recv(1024).decode()
    print(f"Request:\n{request}")

    # 6. Compose a minimal HTTP response: Status-Line, Headers, blank line, Body
    http_response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html\r\n"
        "\r\n"
        "<h1>Hello from Server</h1>"
    )

    # Send the response bytes down the TCP connection
    client_socket.sendall(http_response.encode())

    # 7. Close the connection (HTTP/1.0 style simple behavior)
    client_socket.close()
```

Notes on the code
- `socket.AF_INET` + `socket.SOCK_STREAM` → TCP IPv4 socket.
- `bind(('0.0.0.0', 8080))` makes the server listen on all network interfaces.
- We `recv(1024)` once for simplicity — real servers parse request lines and headers robustly and may read more.
- HTTP response format: status line + CRLF-terminated headers + blank CRLF line + body.
- For simplicity we close the connection after responding.

---

## Part 3 — Experiments

### Experiment A — Local Test 
1. Run the server:
   - `python3 http_server.py`
2. On the same computer open a browser and go to:
   - `http://localhost:8080`  (or `http://127.0.0.1:8080`)
3. Observation:
   - Browser should display "Hello from Server".
   - The Python terminal prints the browser request (including `User-Agent` and `Host` header).

### Experiment B — LAN Test 
1. Keep the server running.
2. Find your computer's local IPv4 address:
   - Windows: `ipconfig`  
   - macOS/Linux: `ifconfig` or `ip addr show`
   - Example: `192.168.1.15`
3. Connect your phone (or another device) to the same Wi‑Fi.
4. In the phone browser go to:
   - `http://<YOUR_COMPUTER_IP>:8080`  e.g. `http://192.168.1.15:8080`
5. Observation:
   - The page should load on the phone. Because the server bound to `0.0.0.0`, it accepted connections from the LAN interface.

### Experiment C — WAN Test 
1. Keep the server running.
2. Disconnect your phone from Wi‑Fi and switch to Cellular or try a friend's server from you browser
3. Try to load:
   - `http://<YOUR_COMPUTER_IP>:8080` (the same local IP from Experiment B)
4. Observation:
   - The browser will fail to connect or time out.
   - Reason: your computer’s local IP (e.g. `192.168.x.x`) is private and not directly reachable from the public cellular network.

---

## Part 4 — Open Questions for Discussion

1. Listening interface vs loopback:
   - If we used `server_socket.bind(('127.0.0.1', 8080))` instead of `0.0.0.0`, why would the phone test fail in Experiment B?
   - Hint: `127.0.0.1` (loopback) only accepts connections from the local machine, not from other devices on the LAN.

2. Why TCP matters for HTML integrity:
   - Consider sending an HTML element split across packets. If packets are lost or reordered (possible with UDP), how could the browser interpret broken HTML like `<h1 Hello</h>`? What visible failures could occur?

3. NAT and private addressing (leads to next topic):
   - In Experiment C you used the same `192.168.x.x` address that worked on Wi‑Fi but failed on Cellular. Does the global Internet know where your laptop is just from that address?
   - If many homes use `192.168.x.x`, how does the Internet differentiate your device from someone else’s? (Hint: this motivates NAT and public IP addresses.)

---

## Extra Activities 

- Improve `http_server.py` to:
  - Serve `index.html` from the current directory instead of sending a hardcoded body.

---

## Summary

You just built a minimal HTTP server over raw TCP. This exercise demonstrates:
- How HTTP relies on TCP’s reliable, ordered stream.
- The difference between binding to `127.0.0.1` (local only) and `0.0.0.0` (all interfaces).
- Why local private addresses work only inside your LAN and how that leads to NAT / public IP concepts.
