# Module 5: The Glass House (Sniffing & Security)

**Objective:**
Today, we are going to prove that the internet is "broken" by default.

1. **The Victim:** We will run a basic HTTP Server with a "Login" page.
2. **The Hacker:** We will write a script to intercept the traffic and steal passwords.
3. **The Fix:** We will upgrade the server to HTTPS (TLS) and watch the hacker fail.

---

## Part 1: The Trap (Unsecured HTTP)

### Theory: The Postcard Analogy

When you use **HTTP** (without the 'S'), you are sending data across the internet like writing on a **Postcard**. Anyone who handles the postcard (the WiFi router, the ISP, the NSA) can read exactly what you wrote. They don't need to "hack" anything; they just have to look at it.

### 🛠️ Step 1: Create the Fake Bank

First, we need a login page. Save this code as `index.html` in your project folder.

**File:** `index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Secure Bank Login</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; padding-top: 50px; background-color: #f0f2f5; }
        .login-box { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
        input { display: block; width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; width: 100%; }
        button:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>MyBank Login</h2>
        <p>🔒 Secure Connection</p>
        <!-- The form sends a POST request to our server -->
        <form action="/" method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
    </div>
</body>
</html>
```

### 🛠️ Step 2: The Victim Server

We need a Python server that can serve this file and accept the login data.

**File:** `victim_server.py`

```python
from http.server import HTTPServer, SimpleHTTPRequestHandler

class MyHandler(SimpleHTTPRequestHandler):
    
    # We override this method to handle the POST request
    def do_POST(self):
        # 1. Get the size of data
        content_length = int(self.headers['Content-Length'])
        # 2. Read the data
        post_data = self.rfile.read(content_length)
        
        # 3. Print it to the Server Console (For us to see)
        print("\n--- SERVER RECEIVED DATA ---")
        print(post_data.decode('utf-8')) 
        print("----------------------------\n")

        # 4. Send a success response
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><h1 style='color:green'>Login Received!</h1><p>Check the SNIFFER terminal...</p></html>")

print("The Victim Server is running on Port 8080...")
httpd = HTTPServer(('0.0.0.0', 8080), MyHandler)
httpd.serve_forever()
```

---

## Part 2: The Hacker (Man-in-the-Middle)

Now, we act as the attacker. We will write a **Proxy Sniffer**. Instead of connecting to the server directly, the victim will connect to *us*, and we will forward their traffic to the real server—while logging everything.

![Man-in-the-Middle Attack](https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Man-in-the-middle_attack.svg/1024px-Man-in-the-middle_attack.svg.png)
*Figure 1: The Man-in-the-Middle (Sniffer) intercepts the data before forwarding it.*

**File:** `sniffer.py`

```python
import socket
import threading

# Configuration
LISTEN_PORT = 9000   # The Hacker's Trap Port
TARGET_HOST = '127.0.0.1'
TARGET_PORT = 8080   # The Real Server Port

def handle_client(client_socket):
    # Connect to the REAL server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((TARGET_HOST, TARGET_PORT))
    except:
        print("❌ Could not connect to the Victim Server!")
        client_socket.close()
        return

    # Start threads to forward data in both directions
    # Client -> Hacker -> Server
    threading.Thread(target=forward, args=(client_socket, server_socket, "REQUEST (Stealing Data)")).start()
    # Server -> Hacker -> Client
    threading.Thread(target=forward, args=(server_socket, client_socket, "RESPONSE")).start()

def forward(source, destination, direction):
    while True:
        try:
            data = source.recv(4096)
            if len(data) == 0: break 

            # --- THE HACK: PRINT THE DATA ---
            try:
                # Try to decode as text to read passwords
                print(f"\n[{direction}]:\n{data.decode('utf-8')}")
            except:
                # If it's binary (images/files), just print raw bytes
                print(f"\n[{direction}]: {data}") 
            # -------------------------------

            destination.send(data)
        except:
            break
    source.close()
    destination.close()

def start_sniffer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', LISTEN_PORT))
    server.listen(5)
    print(f"😈 Sniffer listening on Port {LISTEN_PORT}...")
    
    while True:
        client_sock, addr = server.accept()
        print(f"⚡ Victim connected from {addr}")
        threading.Thread(target=handle_client, args=(client_sock,)).start()

if __name__ == '__main__':
    start_sniffer()
```

### 🧨 The Experiment:

1. Run `victim_server.py` in Terminal 1.
2. Run `sniffer.py` in Terminal 2.
3. Open Browser and go to: `http://localhost:9000` (The Sniffer's port).
4. Enter a Username/Password and click Sign In.
5. **Look at Terminal 2.** You will see the password in **PLAIN TEXT**.

---

## Part 3: The Theory (Alice, Bob, and the Locked Box)

### 1. The Problem: "The Shared Secret"

Imagine Alice wants to send a locked box to Bob. If she locks it with a key, she has to mail the key to Bob too. The postman (Sniffer) can steal the key and open the box later. This is **Symmetric Encryption**.

![Symmetric Encryption](https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Symmetric_key_encryption.svg/800px-Symmetric_key_encryption.svg.png)
*Figure 2: Symmetric Encryption (One key for both locking and unlocking).* 

### 2. The Solution: Asymmetric Encryption

We use two keys: A **Public Key** (locks the box) and a **Private Key** (unlocks the box).

![Asymmetric Encryption](https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Public_key_encryption.svg/800px-Public_key_encryption.svg.png)
*Figure 3: Asymmetric Encryption (Different keys for encryption and decryption).* 

### 3. The Handshake (How TLS Works)

1. **Client Hello:** "I want to talk securely."
2. **Server Hello:** "Here is my Certificate (Public Key)."
3. **Key Exchange:** Client creates a secret password, encrypts it with the Public Key, and sends it back. (The Sniffer cannot read this).
4. **Secure Chat:** Both sides now have the secret password.

---

## Part 4: The Fix (Generating Keys & Enabling TLS)

### Step 1: Generate Keys (Run this once)

We need to generate our own "ID Card" (Certificate) and "Secret Key".

**File:** `generate_keys.py`

```python
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime

# 1. Generate Private Key
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# 2. Generate a Self-Signed Certificate
subject = x509.Name([
    x509.NameAttribute(x509.NameOID.COMMON_NAME, u"localhost"),
])

cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    subject
).public_key(
    key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    datetime.datetime.utcnow() + datetime.timedelta(days=365)
).sign(key, hashes.SHA256(), default_backend())

# 3. Write files to disk
with open("key.pem", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("✅ Created cert.pem (Public ID) and key.pem (Private Secret)!")
```

### Step 2: The Secure Server

We wrap our server socket with the SSL Context.

![TLS Handshake](https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/SSL_handshake_with_two_way_authentication_with_certificates.svg/800px-SSL_handshake_with_two_way_authentication_with_certificates.svg.png)
*Figure 4: The Handshake. 1. Hello 2. Certificate 3. Key Exchange.* 

**File:** `secure_server.py`

```python
import ssl
from http.server import HTTPServer, SimpleHTTPRequestHandler

# --- THEORY NOTE: The SSL Context ---
# The Context is the "Configuration Object" for our security.
# It holds our keys and decides which protocol version to use (TLS).
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

# Load the "ID Card" (Certificate) and the "Secret Mind" (Private Key)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

class SecureHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        # 1. Receive Data (This data is ALREADY decrypted by the wrapper!)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        print("\n🔒 SECURE SERVER RECEIVED DATA (Decrypted):")
        print(post_data.decode('utf-8')) 
        print("-------------------------------------------\n")

        # 2. Send Response (The wrapper will Encrypt this automatically)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<html><h1 style='color:green'>Secure Login Success!</h1></html>")

print("🔒 SECURE Server running on Port 8080 (HTTPS)...")

# 1. Create the Standard HTTP Server (Unsecured)
httpd = HTTPServer(('0.0.0.0', 8080), SecureHandler)

# 2. THE WRAPPER (The Magic Line)
# We take the standard socket (httpd.socket) and wrap it inside our SSL Context.
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

# 3. Start Listening
httpd.serve_forever()
```

### 🧨 The Final Test:

1. Run `secure_server.py`.
2. Run `sniffer.py`.
3. Go to `https://localhost:8080` directly.
4. Now try going through the Sniffer: `http://localhost:9000`.
5. Check the Sniffer terminal. You will see unreadable **GARBAGE** (Encrypted bytes).

---

## Summary

You've now experienced:
- ✅ **HTTP Vulnerability:** How unencrypted traffic can be intercepted
- ✅ **Man-in-the-Middle Attacks:** Building a proxy sniffer
- ✅ **Encryption Theory:** Symmetric vs. Asymmetric encryption
- ✅ **TLS/HTTPS Implementation:** Wrapping sockets with SSL contexts
- ✅ **Security Validation:** Proving encryption works by watching the sniffer fail

**Next Steps:** Explore certificate authorities, DNSSEC, and VPNs to understand how these security principles scale across the entire internet.
