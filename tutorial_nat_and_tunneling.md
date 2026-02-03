# Notebook 4: The Connectivity Challenge (NAT & Tunnels)

**Prerequisites:** You must have your `http_server.py` from the previous lesson ready.

---

## 1. The "Localhost Trap"

In our last session, you built a web server. You accessed it by typing `http://localhost:8080` or `http://127.0.0.1:8080` in your browser. It worked perfectly.

**The Experiment:**
If you copy that link and send it to a classmate in the chat right now, **it will fail for them.**

**The Mystery:**
Why can you see your server, but nobody else can? You are both on the internet, so why can't you talk?

To answer this, we need to understand the difference between **Private** and **Public** networks.

---

## 2. The Two Identities: Public vs. Private IPs

Your computer actually has *two* IP addresses.

### A. Private IP (Local)
This is your address *inside* your home WiFi network.
* **Format:** Usually starts with `192.168.x.x` or `10.0.x.x`.
* **Scope:** Only visible to devices in your house (your phone, your printer, your TV).
* **Analogy:** This is like your "Room Number" inside a hotel. If you tell a delivery driver "I am in Room 202," they can't find you unless they are already inside the hotel.

### B. Public IP (Global)
This is the address your Internet Service Provider (ISP) assigns to your **Home Router**.
* **Format:** Random looking numbers (e.g., `85.203.x.x`).
* **Scope:** Visible to the entire internet.
* **Analogy:** This is the street address of the hotel (e.g., "123 Beach Road").

### 🐍 Code Experiment: Find your Local IP
Let's ask Python what it thinks your IP address is. Run this code:

```python
import socket

def get_local_ip():
    try:
        # We connect to a public DNS (Google's 8.8.8.8) just to see 
        # which network interface our computer uses.
        # We don't actually send data, so this is safe and fast.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error: {e}"

print(f"🏠 My Local (Private) IP is: {get_local_ip()}")
```

---

## 3. The Guard Dog: Network Address Translation (NAT)

If your computer has a Private IP (e.g., `192.168.1.5`), how does it talk to Google? Google can't send data back to `192.168.1.5` because millions of homes use that exact same private IP!

This is where your **Home Router** performs a trick called **NAT**.

**How NAT Works:**
1. **Outgoing:** When you send a request, your Router pauses the packet. It replaces your **Private IP** with its own **Public IP** and assigns a specific "port" to remember you.
2. **Incoming:** When the reply comes back to the Router, it checks its memory: *"Oh, this packet on port 54321? That belongs to the computer at 192.168.1.5."*
3. **Translation:** It swaps the address back and forwards the packet to you.

### 🐍 Code Experiment: Find your Public IP
Your computer doesn't actually know its Public IP—only the Router knows. To find it, we have to ask an external server "Who do you see me as?"

```python
import urllib.request

def get_public_ip():
    try:
        # 'ident.me' is a simple service that returns your IP as plain text
        # If this fails, try 'http://icanhazip.com'
        url = "https://ident.me" 
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return "Could not determine public IP"

print(f"🌍 My Public (Global) IP is: {get_public_ip()}")
```

**🛑 Checkpoint**
Compare your Local IP and Public IP. Are they different?
* **If Yes:** You are behind a NAT (this is good!).
* **If No:** You are directly connected to the internet (rare and dangerous for home PCs).

---

## 4. The Solution: Tunneling

We have a problem. We want our classmates to see our server. Normally, you would log into your router and configure **Port Forwarding**.

**Why we will NOT do Port Forwarding today:**
1. **Risk:** You are at home. Messing with router settings can break the internet for your whole family.
2. **ISP Blocks:** Many home internet providers use "Carrier Grade NAT," which makes port forwarding impossible anyway.

**The Fix: Tunneling with ngrok**
We will use a tool called **ngrok**. It creates a secure tunnel from the public internet directly to your laptop, drilling through the NAT.

### 🛠️ Lab Activity: Expose your Server

**Step 1: Get the Tool**
1. Go to [ngrok.com](https://ngrok.com) and sign up (it's free).
2. Download the version for your OS (Windows/Mac/Linux).
3. Connect your account by running the command shown on their dashboard:
   ```bash
   ngrok config add-authtoken <YOUR_TOKEN>
   ```

**Step 2: Start your Server**
Run your `http_server.py` from the last lesson. Ensure it is listening on port 8080.
```bash
# Run this in your terminal:
python3 http_server.py
```

**Step 3: Open the Tunnel**
Open a **new** terminal window (keep the server running in the first one) and type:
```bash
ngrok http 8080
```

**Step 4: The Magic Link**
Ngrok will show you a "Forwarding" link that looks like `https://a1b2-c3d4.ngrok-free.app`.
1. Copy that link.
2. **Test it:** Turn off WiFi on your phone (use 4G/5G). Open the link.
3. **Success:** You should see your server response!

---

## 5. Homework: The "Global Hello" Relay

Since we are an online class, let's use our distance to our advantage.

**The Mission:** You must log a visit from a classmate who is in a different physical location.

**Instructions:**

1. **Modify your Code:** Update your `http_server.py` to print a visible message when someone visits.
   ```python
   # Inside your while True loop or handler:
   print(f"🔔 DING! Someone accessed path: {request_line}")
   ```

2. **Go Live:** Run your server and run `ngrok http 8080`.
3. **Share:** Paste your ngrok link in the Class Chat.
4. **Visit:** Click on a link from a classmate.
5. **Verify:**
   * **As the Visitor:** Did you see their HTML page?
   * **As the Host:** Check your terminal. Did you see the print statement?

### 🧠 Advanced Question (For Discussion)
When you look at your server logs, the connection seems to come from `127.0.0.1` (localhost), even though your friend is miles away. Why?
*Hint: Who is your Python server actually talking to? Your friend, or the ngrok software running on your computer?*