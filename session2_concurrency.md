# Session 2 — Concurrency & The Chat Room

Welcome to Session 2! Today we graduate from "Toy Networking" to "Real-World Networking".

In Session 1, we built an Echo Server that could handle... exactly one person at a time. Today, we break that limit.

## Goals
1.  **Understand Blocking**: Why did our first server freeze when a second person tried to join?
2.  **Multithreading**: Using Python's `threading` to handle many clients at once.
3.  **Broadcast Chat**: Building a real chat room where everyone sees everyone's messages.
4.  **Finding Yourself**: How to find your local IP to let others connect to you.

---

## Part 1: The "Blocking" Problem

Recall our simple server loop:

```python
conn, addr = s.accept() # Stops here until someone calls
while True:
    data = conn.recv(1024) # Stops here until data arrives
    # ... process data ...
```

Because the code "stops" (blocks) at `recv()`, the server is 100% focused on that one client. It cannot go back to `accept()` to welcome a new user. It's like a receptionist who goes on a 3-hour lunch with the first visitor, ignoring the ringing phone.

**The Solution:** Hire more receptionists! (Threads).

---

## Part 2: Multithreading

We will use Python's `threading` module. Instead of handling the client in the main loop, we pass the client connection to a separate "worker thread" and immediately go back to listening for new connections.

### Exercise 1: Run the `threaded_echo_server.py`
1.  Start the server.
2.  Open **3 separate terminals**.
3.  Run `echo_client.py` (from Session 1) in all three.
4.  Notice they all work simultaneously!

---

## Part 3: The Chat Room (Shared State)

Now that we have threads, we need them to talk to each other. If Alice sends a message to Thread A, Thread A needs to tell Thread B (Bob) and Thread C (Charlie).

**Architecture:**
1.  **Global List**: A list `clients = []` stores all active connections.
2.  **Broadcast**: When a message comes in, loop through `clients` and send it to everyone else.
3.  **Cleanup**: If a client disconnects, remove them from the list immediately.

### Exercise 2: The Chat Room
1.  Run `simple_chat_server.py`.
2.  Run `threaded_chat_client.py` in multiple terminals.
3.  Chat away!

**Why a special client?**
Standard `input()` blocks your code. You can't receive a message while typing one! Our `threaded_chat_client.py` uses two threads: one for typing, one for listening.

---

## Part 4: How do I find my IP? (Connecting Real Computers)

To play with a friend, `127.0.0.1` won't work (that only means "myself"). You need your **LAN IP**.

1.  **Windows**: Open cmd, type `ipconfig`. Look for "IPv4 Address" (usually `192.168.x.x` or `10.x.x.x`).
2.  **Mac/Linux**: Open terminal, type `ifconfig` or `ip a`. Look for `en0` or `wlan0`.

**How did you get this IP?**
Your router acts as a **DHCP Server** (Dynamic Host Configuration Protocol). When you joined the WiFi, your laptop shouted "I need an IP!", and the router replied "Here, take 192.168.1.5 for 24 hours."

---

## Advanced Challenge: The "Stream" Reality

You might notice sometimes messages get stuck together (`HelloHowAreYou`). This is because TCP is a **stream**, not a packet queue.
*   **Next Level**: Implement a "Protocol" using 4 bytes to say how long the message is, so you never cut a message in half.

Happy Coding!