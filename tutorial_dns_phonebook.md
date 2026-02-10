# Notebook 5: The Internet's Phonebook (DNS Deep Dive)

**Prerequisites:** Understanding of IP addresses from previous lessons.

---

## 1. The Mystery of the Vanishing Numbers

**Quick Experiment:** Open your terminal and type:
```bash
ping google.com
```

Look at the first line. You'll see something like:
```
PING google.com (142.250.185.46): 56 data bytes
```

**The Question:** You typed `google.com`, but your computer is sending packets to `142.250.185.46`. 

**The Mystery:** 
- Computers only speak in IP addresses (numbers).
- Humans prefer names (words).
- Who did the translation? And how fast did they do it?

Try this:
```bash
ping facebook.com
ping youtube.com
ping github.com
```

**Notice:** Every single time, a name instantly becomes a number. There's a massive, invisible system working behind every click you make.

Today, we reverse-engineer the **Domain Name System (DNS)** — the Internet's phonebook.

---

## 2. Why DNS Exists: A Historical Problem

### The Old Way (1970s - Early ARPANET)

Before DNS, there was a single text file called `HOSTS.TXT`:

```
# This file lived on a server at Stanford Research Institute
10.0.0.1    UCLA-HOST
10.0.0.2    SRI-HOST
10.0.0.3    MIT-HOST
```

**The Process:**
1. Every computer on the internet downloaded this file.
2. When you wanted to visit `MIT-HOST`, your computer looked it up locally.
3. When a new computer joined the internet, someone manually updated `HOSTS.TXT`.
4. Everyone re-downloaded the file.

**The Breaking Point:**
- In 1983, ARPANET had about 1,000 computers.
- The file was updated **every single day**.
- Download times were increasing.
- Name conflicts were common (two places wanted the same name).

**The Solution (1984):**
Paul Mockapetris invented DNS — a **distributed, hierarchical database** where no single file contains all the answers.

---

## 3. How DNS Really Works: The Treasure Hunt

When you type `www.github.com` in your browser, your computer doesn't know the IP. It has to **ask around**. But it asks in a very specific order.

### The DNS Hierarchy (Top-Down View)

```
                        . (root)
                        |
        +---------------+---------------+
        |               |               |
      .com            .org            .net
        |               |               |
    github.com      wikipedia.org   example.net
        |
    www.github.com
```

**Key Insight:** DNS is like a tree. Each "dot" in a domain name represents going one level deeper.

### The 4-Step Resolution Process

Let's trace what happens when you visit `www.github.com`:

#### **Step 0: Check Your Cache**
Your computer is lazy (in a good way). Before asking anyone, it checks:
1. **Browser cache:** "Did I visit this site in the last few minutes?"
2. **OS cache:** "Did any application on this computer recently look this up?"
3. **Local hosts file:** Is there a manual override in `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows)?

If found → Done! If not → Continue to Step 1.

#### **Step 1: Ask Your Recursive Resolver (Your ISP's DNS Server)**
```
Your Computer: "Hey, what's the IP for www.github.com?"
ISP DNS Server: "Let me check my cache... Nope, don't have it. 
                 I'll find out for you. Hold on."
```

**Important:** This server does the "hunting" for you. You asked one question; it will ask four more on your behalf.

#### **Step 2: Ask a Root Server**
```
ISP DNS Server → Root Server: "Where can I find .com domains?"
Root Server: "I don't know about github.com specifically, 
              but all .com questions go to these servers: 
              [list of .com nameservers]"
```

**Fun Fact:** There are only **13 root server addresses** in the world (though each is actually a cluster of hundreds of physical servers). They are named `a.root-servers.net` through `m.root-servers.net`.

#### **Step 3: Ask the TLD (Top-Level Domain) Server**
```
ISP DNS Server → .com TLD Server: "Where can I find github.com?"
.com Server: "I don't handle subdomains, but github.com's 
              nameservers are: ns1.github.com, ns2.github.com..."
```

**What are TLDs?**
- `.com` (commercial)
- `.org` (organization)
- `.edu` (education)
- `.io` (Indian Ocean territory, but popular with startups)
- Country codes: `.uk`, `.de`, `.jp`

#### **Step 4: Ask the Authoritative Server**
```
ISP DNS Server → ns1.github.com: "What's the IP for www.github.com?"
GitHub's DNS: "That's 140.82.121.4"
```

**Authoritative means:** This server is the **official source of truth** for github.com. Whatever it says is final.

#### **Step 5: Return the Answer**
```
ISP DNS Server → Your Computer: "www.github.com is 140.82.121.4"
Your Computer: "Thanks! [stores in cache] [connects to 140.82.121.4]"
```

### 🐍 Code Experiment: See the Steps in Action

Python's `socket` library hides all this complexity. Let's do a simple lookup first:

```python
import socket

def simple_dns_lookup(domain):
    """
    This is what happens "under the hood" when you use a URL.
    Python asks the OS, the OS asks the configured DNS server,
    and eventually you get back an IP address.
    """
    try:
        ip_address = socket.gethostbyname(domain)
        print(f"✅ {domain} → {ip_address}")
        return ip_address
    except socket.gaierror as e:
        print(f"❌ Failed to resolve {domain}: {e}")
        return None

# Test it with various domains
domains = ["google.com", "github.com", "nonexistent-site-xyz123.com"]

for domain in domains:
    simple_dns_lookup(domain)
```

**What you'll see:**
```
✅ google.com → 142.250.185.46
✅ github.com → 140.82.121.4
❌ Failed to resolve nonexistent-site-xyz123.com: [Errno 8] nodename nor servname provided, or not known
```

**Behind the scenes:** That one line `socket.gethostbyname()` just did all 5 steps we described!

---

## 4. DNS Record Types: The Phonebook's Columns

A DNS server doesn't just store "name → IP". It stores many types of records.

### Common DNS Record Types

| Record Type | Purpose | Example |
|-------------|---------|---------|
| **A** | Maps domain to IPv4 address | `github.com → 140.82.121.4` |
| **AAAA** | Maps domain to IPv6 address | `github.com → 2606:50c0:8000::153` |
| **CNAME** | Alias (points one name to another) | `www.example.com → example.com` |
| **MX** | Mail server | `gmail.com → aspmx.l.google.com` |
| **TXT** | Text notes (used for verification) | `"google-site-verification=abc123"` |
| **NS** | Nameserver (who is authoritative) | `github.com → ns1.github.com` |

### 🐍 Code Experiment: Query Different Record Types

For this, we need a more powerful library. Install it first:
```bash
pip install dnspython
```

Now let's write a DNS detective tool:

```python
import dns.resolver

def dns_detective(domain, record_type='A'):
    """
    Query DNS for specific record types.
    
    Args:
        domain (str): The domain to look up (e.g., 'github.com')
        record_type (str): Type of DNS record (A, AAAA, MX, TXT, NS, CNAME)
    
    Returns:
        list: All records found for that type
    """
    try:
        # Create a resolver object (this is like your ISP's DNS server)
        resolver = dns.resolver.Resolver()
        
        # Query the DNS system
        answers = resolver.resolve(domain, record_type)
        
        print(f"\n🔍 Query: {domain} ({record_type} records)")
        print("=" * 50)
        
        results = []
        for rdata in answers:
            results.append(str(rdata))
            print(f"  → {rdata}")
        
        return results
    
    except dns.resolver.NXDOMAIN:
        print(f"❌ Domain {domain} does not exist")
        return []
    except dns.resolver.NoAnswer:
        print(f"⚠️  {domain} has no {record_type} records")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

# Example 1: Basic A record lookup
dns_detective("github.com", "A")

# Example 2: IPv6 addresses
dns_detective("github.com", "AAAA")

# Example 3: Mail servers (MX records)
dns_detective("gmail.com", "MX")

# Example 4: Nameservers (who's in charge?)
dns_detective("github.com", "NS")

# Example 5: TXT records (often used for verification)
dns_detective("github.com", "TXT")
```

**What you'll discover:**

```
🔍 Query: github.com (A records)
==================================================
  → 140.82.121.4

🔍 Query: github.com (AAAA records)
==================================================
  → 2606:50c0:8000::153

🔍 Query: gmail.com (MX records)
==================================================
  → 5 gmail-smtp-in.l.google.com.
  → 10 alt1.gmail-smtp-in.l.google.com.
  → 20 alt2.gmail-smtp-in.l.google.com.

🔍 Query: github.com (NS records)
==================================================
  → ns1.github.com.
  → ns2.github.com.
  → ns3.github.com.
```

**Notice the MX records have numbers (5, 10, 20)?**
That's **priority**. The mail server tries `5` first. If it fails, it tries `10`, then `20`. This is a built-in backup system!

---

## 5. DNS Caching: Speed vs. Freshness

### The Tradeoff Problem

Imagine if every time you clicked "refresh" on github.com, your computer had to:
1. Ask the ISP DNS server
2. Which asks the root server
3. Which asks the .com server
4. Which asks GitHub's server

That would take **seconds** per page load, and would **overload** the root servers.

**The Solution: Caching**

Every DNS record comes with a **TTL (Time To Live)** — a timer that says "you can trust this answer for X seconds."

### 🐍 Code Experiment: See TTL in Action

```python
import dns.resolver
import time

def check_dns_caching(domain, record_type='A'):
    """
    Query DNS and show TTL (Time To Live) values.
    TTL tells you how long you can cache this answer.
    """
    resolver = dns.resolver.Resolver()
    
    print(f"\n🕐 First Query for {domain}:")
    print("=" * 50)
    
    # First query (might be slow - going through full resolution)
    start_time = time.time()
    answers = resolver.resolve(domain, record_type)
    first_query_time = time.time() - start_time
    
    for rdata in answers:
        print(f"  IP: {rdata}")
        print(f"  TTL: {answers.rrset.ttl} seconds")
        print(f"  Query time: {first_query_time*1000:.2f} ms")
    
    print(f"\n⏳ Waiting 2 seconds, then querying again...")
    time.sleep(2)
    
    # Second query (should be faster - cached)
    start_time = time.time()
    answers = resolver.resolve(domain, record_type)
    second_query_time = time.time() - start_time
    
    print(f"\n🕐 Second Query for {domain}:")
    print("=" * 50)
    for rdata in answers:
        print(f"  IP: {rdata}")
        print(f"  TTL: {answers.rrset.ttl} seconds (decreased by ~2)")
        print(f"  Query time: {second_query_time*1000:.2f} ms")
    
    print(f"\n📊 Speed Comparison:")
    print(f"  First query:  {first_query_time*1000:.2f} ms")
    print(f"  Second query: {second_query_time*1000:.2f} ms")
    print(f"  Speedup: {first_query_time/second_query_time:.1f}x faster")

# Try it!
check_dns_caching("github.com")
```

**What you'll see:**
```
🕐 First Query for github.com:
==================================================
  IP: 140.82.121.4
  TTL: 60 seconds
  Query time: 45.23 ms

⏳ Waiting 2 seconds, then querying again...

🕐 Second Query for github.com:
==================================================
  IP: 140.82.121.4
  TTL: 58 seconds (decreased by ~2)
  Query time: 0.15 ms

📊 Speed Comparison:
  First query:  45.23 ms
  Second query: 0.15 ms
  Speedup: 301.5x faster
```

**Key Observations:**
1. The TTL **decreased** by 2 seconds (the time we waited)
2. The second query was **300x faster** (cached!)
3. After 60 seconds, the cache expires and you'd have to ask again

### Cache Poisoning Attack (Why Security Matters)

**The Threat:**
An attacker tricks your DNS cache into storing:
```
google.com → 6.6.6.6 (attacker's server)
```

Now when you type `google.com`, you go to the attacker's fake site!

**The Defense:**
- **DNSSEC:** Digital signatures verify DNS answers
- **DNS over HTTPS (DoH):** Encrypts DNS queries so ISPs can't spy or tamper
- **DNS over TLS (DoT):** Similar encryption protection

---

## 6. Build Your Own: A Simple DNS Client

Let's create a tool that mimics what `nslookup` or `dig` does:

```python
import dns.resolver
import dns.reversename
import socket

class SimpleDNSClient:
    """
    A beginner-friendly DNS lookup tool.
    This shows you what's happening when you use a domain name.
    """
    
    def __init__(self):
        # Use Google's public DNS (8.8.8.8) instead of your ISP's
        # This is useful for consistency and avoiding censorship
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # Google and Cloudflare
    
    def lookup(self, domain):
        """
        Perform multiple DNS queries and present the results clearly.
        """
        print(f"\n{'='*60}")
        print(f"🔍 DNS INVESTIGATION: {domain}")
        print(f"{'='*60}")
        
        # 1. Basic A record (IPv4)
        print("\n📍 IPv4 Address (A Record):")
        try:
            answers = self.resolver.resolve(domain, 'A')
            for rdata in answers:
                print(f"   → {rdata} (TTL: {answers.rrset.ttl}s)")
        except Exception as e:
            print(f"   ❌ Not found: {e}")
        
        # 2. IPv6 address (AAAA record)
        print("\n📍 IPv6 Address (AAAA Record):")
        try:
            answers = self.resolver.resolve(domain, 'AAAA')
            for rdata in answers:
                print(f"   → {rdata}")
        except Exception as e:
            print(f"   ⚠️  No IPv6 address")
        
        # 3. Nameservers (who's in charge?)
        print("\n🏢 Authoritative Nameservers (NS Records):")
        try:
            answers = self.resolver.resolve(domain, 'NS')
            for rdata in answers:
                print(f"   → {rdata}")
        except Exception as e:
            print(f"   ❌ Not found: {e}")
        
        # 4. Mail servers
        print("\n📧 Mail Servers (MX Records):")
        try:
            answers = self.resolver.resolve(domain, 'MX')
            # Sort by priority (lower number = higher priority)
            mx_records = [(r.preference, str(r.exchange)) for r in answers]
            mx_records.sort()
            for priority, server in mx_records:
                print(f"   → Priority {priority}: {server}")
        except Exception as e:
            print(f"   ⚠️  No mail servers configured")
        
        # 5. TXT records (verification, SPF, etc.)
        print("\n📝 Text Records (TXT):")
        try:
            answers = self.resolver.resolve(domain, 'TXT')
            for rdata in answers:
                # TXT records can be long, so truncate for display
                txt = str(rdata)
                if len(txt) > 80:
                    txt = txt[:77] + "..."
                print(f"   → {txt}")
        except Exception as e:
            print(f"   ⚠️  No TXT records")
        
        # 6. CNAME (alias check)
        print("\n🔗 Aliases (CNAME Records):")
        try:
            answers = self.resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                print(f"   → {domain} is an alias for {rdata}")
        except Exception as e:
            print(f"   ℹ️  Not an alias (no CNAME)")
        
        print(f"\n{'='*60}\n")
    
    def reverse_lookup(self, ip_address):
        """
        Given an IP, find the domain name (if any).
        This is called "reverse DNS" or "PTR record lookup."
        """
        print(f"\n🔄 Reverse Lookup: {ip_address}")
        try:
            # Convert IP to special format (e.g., 1.2.3.4 → 4.3.2.1.in-addr.arpa)
            addr = dns.reversename.from_address(ip_address)
            answers = self.resolver.resolve(addr, 'PTR')
            for rdata in answers:
                print(f"   → {ip_address} belongs to: {rdata}")
        except Exception as e:
            print(f"   ⚠️  No reverse DNS entry")

# Let's use our tool!
client = SimpleDNSClient()

# Test with various domains
client.lookup("github.com")
client.lookup("google.com")
client.lookup("wikipedia.org")

# Reverse lookup (IP → Domain)
client.reverse_lookup("8.8.8.8")  # Google's DNS server
client.reverse_lookup("1.1.1.1")  # Cloudflare's DNS server
```

**Sample Output:**
```
============================================================
🔍 DNS INVESTIGATION: github.com
============================================================

📍 IPv4 Address (A Record):
   → 140.82.121.4 (TTL: 60s)

📍 IPv6 Address (AAAA Record):
   → 2606:50c0:8000::153

🏢 Authoritative Nameservers (NS Records):
   → ns1.github.com.
   → ns2.github.com.
   → ns3.github.com.

📧 Mail Servers (MX Records):
   → Priority 1: aspmx.l.google.com.
   → Priority 5: alt1.aspmx.l.google.com.

📝 Text Records (TXT):
   → "v=spf1 include:_spf.google.com ~all"
   → "google-site-verification=abc123..."

🔗 Aliases (CNAME Records):
   ℹ️  Not an alias (no CNAME)

============================================================

🔄 Reverse Lookup: 8.8.8.8
   → 8.8.8.8 belongs to: dns.google.
```

---

## 7. DNS in the Real World: Why It Matters

### Case Study 1: The Great DDoS of 2016

**What Happened:**
On October 21, 2016, a company called **Dyn** (a major DNS provider) was attacked. Millions of IoT devices (security cameras, DVRs) were hacked and flooded Dyn's servers with traffic.

**The Impact:**
- Twitter, Netflix, Reddit, GitHub, Spotify all went **offline**
- Not because their servers were down
- But because **DNS couldn't translate their names to IPs**

**The Lesson:**
DNS is a **single point of failure**. If DNS dies, the internet dies — even if every website is still running.

### Case Study 2: China's DNS Hijacking (2010)

**What Happened:**
For 17 minutes, a Chinese ISP "announced" to the world: *"I am the authoritative server for .com, .net, .org"*

**The Impact:**
- 15% of global internet traffic was redirected through China
- Domains like `.gov` and `.mil` (US government/military) were affected

**The Lesson:**
DNS relies on **trust**. There's no built-in verification (unless you use DNSSEC).

### Case Study 3: DNS Speed = Website Speed

Amazon found that **every 100ms of latency costs them 1% of sales**.

DNS lookup is often the **first step** in loading a page:
1. DNS lookup: 20-120ms
2. TCP connection: 50ms
3. TLS handshake: 100ms
4. HTTP request: 50ms

**The Lesson:**
Fast DNS = Fast websites. This is why companies use:
- **Cloudflare** (1.1.1.1) — claims to be the fastest
- **Google** (8.8.8.8) — highly cached
- **Local caching** — your computer remembers

---

## 8. Advanced Experiment: Measure DNS Performance

Let's benchmark different DNS providers:

```python
import dns.resolver
import time

def benchmark_dns_provider(dns_server, test_domains):
    """
    Measure how fast a DNS server responds.
    
    Args:
        dns_server (str): IP of DNS server (e.g., '8.8.8.8')
        test_domains (list): Domains to look up
    
    Returns:
        dict: Average response time and success rate
    """
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    resolver.timeout = 2  # 2 second timeout
    resolver.lifetime = 2
    
    times = []
    failures = 0
    
    print(f"\n🔬 Testing DNS Server: {dns_server}")
    print("-" * 50)
    
    for domain in test_domains:
        try:
            start = time.time()
            resolver.resolve(domain, 'A')
            elapsed = (time.time() - start) * 1000  # Convert to milliseconds
            times.append(elapsed)
            print(f"  ✓ {domain:20s} → {elapsed:6.2f} ms")
        except Exception as e:
            failures += 1
            print(f"  ✗ {domain:20s} → FAILED")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n📊 Results:")
        print(f"  Average: {avg_time:.2f} ms")
        print(f"  Fastest: {min(times):.2f} ms")
        print(f"  Slowest: {max(times):.2f} ms")
        print(f"  Success: {len(times)}/{len(test_domains)}")
        return {"avg": avg_time, "success_rate": len(times)/len(test_domains)}
    else:
        print(f"❌ All queries failed")
        return {"avg": 999999, "success_rate": 0}

# Test domains (mix of popular and niche sites)
test_domains = [
    "google.com",
    "github.com",
    "youtube.com",
    "wikipedia.org",
    "amazon.com",
    "reddit.com",
    "stackoverflow.com",
    "twitter.com"
]

# Popular DNS providers
dns_providers = {
    "Google Primary": "8.8.8.8",
    "Google Secondary": "8.8.4.4",
    "Cloudflare": "1.1.1.1",
    "Quad9": "9.9.9.9",
    "OpenDNS": "208.67.222.222"
}

# Benchmark each one
results = {}
for name, server in dns_providers.items():
    results[name] = benchmark_dns_provider(server, test_domains)
    time.sleep(1)  # Be nice, don't hammer servers

# Compare
print("\n\n🏆 FINAL RANKINGS")
print("=" * 60)
sorted_results = sorted(results.items(), key=lambda x: x[1]['avg'])
for rank, (name, data) in enumerate(sorted_results, 1):
    print(f"{rank}. {name:20s} → {data['avg']:6.2f} ms (avg)")
```

**Sample Output:**
```
🏆 FINAL RANKINGS
============================================================
1. Cloudflare          →  18.34 ms (avg)
2. Google Primary      →  22.17 ms (avg)
3. Quad9               →  24.89 ms (avg)
4. Google Secondary    →  25.01 ms (avg)
5. OpenDNS             →  31.45 ms (avg)
```

**What this tells you:**
- **Geographic location matters** (servers closer to you are faster)
- **Your results will differ** based on where you live
- The "fastest" DNS isn't always the best (privacy, filtering features also matter)

---

## 9. Homework: The DNS Detective Challenge

### Mission 1: Find the Hidden IP

Some websites use **multiple IPs** for load balancing. Each time you query, you might get a different answer.

**Task:**
Write a script that queries `google.com` 10 times and collects all unique IPs.

**Starter Code:**
```python
import dns.resolver
import time

def find_all_ips(domain, num_queries=10):
    """
    Query a domain multiple times to discover all possible IPs.
    Some sites use round-robin DNS for load balancing.
    """
    resolver = dns.resolver.Resolver()
    unique_ips = set()  # Use a set to automatically remove duplicates
    
    for i in range(num_queries):
        try:
            answers = resolver.resolve(domain, 'A')
            for rdata in answers:
                unique_ips.add(str(rdata))
        except Exception as e:
            print(f"Query {i+1} failed: {e}")
        
        time.sleep(0.5)  # Small delay between queries
    
    return unique_ips

# Test it!
ips = find_all_ips("google.com", 10)
print(f"\n🎯 Found {len(ips)} unique IP(s) for google.com:")
for ip in sorted(ips):
    print(f"  → {ip}")
```

**Questions to answer:**
1. How many unique IPs did you find?
2. Do they all belong to the same network (check the first two octets)?
3. Try with `facebook.com`, `netflix.com` — do they also use multiple IPs?

---

### Mission 2: The Propagation Test

When you change a DNS record, it doesn't update instantly worldwide. This is called **DNS propagation**.

**Scenario:**
Imagine you just bought a domain `mycoolsite.com` and pointed it to IP `1.2.3.4`. You need to know when the change has spread globally.

**Task:**
Write a script that queries DNS servers in different countries to see if they all return the same IP.

**Starter Code:**
```python
import dns.resolver

def check_global_propagation(domain, expected_ip):
    """
    Check if a DNS change has propagated to different DNS servers.
    We'll use public DNS servers from different providers/regions.
    """
    dns_servers = {
        "Cloudflare (Global)": "1.1.1.1",
        "Google (Global)": "8.8.8.8",
        "Quad9 (Global)": "9.9.9.9",
        "OpenDNS (US)": "208.67.222.222",
        "AdGuard (Global)": "94.140.14.14"
    }
    
    print(f"\n🌍 Checking propagation for {domain}")
    print(f"   Expected IP: {expected_ip}")
    print("=" * 60)
    
    results = {}
    for name, server in dns_servers.items():
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [server]
        
        try:
            answers = resolver.resolve(domain, 'A')
            ip = str(answers[0])
            results[name] = ip
            
            if ip == expected_ip:
                status = "✅ Correct"
            else:
                status = f"⚠️  Shows {ip} (not propagated yet)"
            
            print(f"{name:25s} → {status}")
        except Exception as e:
            print(f"{name:25s} → ❌ Failed: {e}")
    
    # Summary
    correct_count = sum(1 for ip in results.values() if ip == expected_ip)
    total_count = len(results)
    
    print(f"\n📊 Propagation: {correct_count}/{total_count} servers updated")
    
    if correct_count == total_count:
        print("🎉 Fully propagated!")
    else:
        print("⏳ Still propagating... check again in 10-60 minutes")
    
    return results

# Example usage:
# check_global_propagation("github.com", "140.82.121.4")

# For your own domain:
# check_global_propagation("yournewdomain.com", "your.server.ip.here")
```

**Your Task:**
1. Pick a domain you control (or use a free service like afraid.org)
2. Change its IP address
3. Run this script every 10 minutes
4. Record how long it takes for all servers to show the new IP

**Expected result:** Most DNS changes take 5 minutes to 24 hours depending on TTL.

---

### Mission 3: Build a Local DNS Cache

**Challenge:** Create a simple DNS cache in Python that:
1. Checks a local dictionary first (cache)
2. If not found, queries real DNS
3. Stores the result with a timestamp
4. Expires entries after 60 seconds

**Starter Code:**
```python
import dns.resolver
import time

class LocalDNSCache:
    """
    A simple DNS cache to avoid repeated lookups.
    Real browsers and OSes do this automatically.
    """
    
    def __init__(self, ttl=60):
        self.cache = {}  # Format: {domain: (ip, timestamp)}
        self.ttl = ttl   # Time To Live in seconds
        self.resolver = dns.resolver.Resolver()
    
    def lookup(self, domain):
        """
        Look up a domain, using cache if available and not expired.
        """
        current_time = time.time()
        
        # Check if we have it in cache
        if domain in self.cache:
            ip, timestamp = self.cache[domain]
            age = current_time - timestamp
            
            if age < self.ttl:
                print(f"💨 CACHE HIT: {domain} → {ip} (age: {age:.1f}s)")
                return ip
            else:
                print(f"⏰ CACHE EXPIRED: {domain} (age: {age:.1f}s)")
        
        # Not in cache or expired — do real DNS lookup
        print(f"🌐 QUERYING DNS: {domain}")
        try:
            answers = self.resolver.resolve(domain, 'A')
            ip = str(answers[0])
            
            # Store in cache
            self.cache[domain] = (ip, current_time)
            print(f"✅ RESOLVED: {domain} → {ip}")
            return ip
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return None
    
    def clear_cache(self):
        """
        Manually clear all cached entries.
        """
        self.cache = {}
        print("🗑️  Cache cleared")
    
    def show_cache(self):
        """
        Display all cached entries and their ages.
        """
        current_time = time.time()
        print("\n📋 Current Cache Contents:")
        if not self.cache:
            print("  (empty)")
        for domain, (ip, timestamp) in self.cache.items():
            age = current_time - timestamp
            remaining = self.ttl - age
            print(f"  {domain:20s} → {ip:15s} (expires in {remaining:.0f}s)")

# Test the cache
cache = LocalDNSCache(ttl=60)

print("=== First lookup (will be slow) ===")
cache.lookup("github.com")

print("\n=== Second lookup (should be instant) ===")
cache.lookup("github.com")

print("\n=== Add more domains ===")
cache.lookup("google.com")
cache.lookup("stackoverflow.com")

cache.show_cache()

print("\n=== Wait 3 seconds and check again ===")
time.sleep(3)
cache.lookup("github.com")  # Should still be cached

print("\n=== Simulate 61 seconds passing ===")
# Manually expire by changing timestamp (for testing)
if "github.com" in cache.cache:
    ip, _ = cache.cache["github.com"]
    cache.cache["github.com"] = (ip, time.time() - 61)

cache.lookup("github.com")  # Should query DNS again
```

**Expected Output:**
```
=== First lookup (will be slow) ===
🌐 QUERYING DNS: github.com
✅ RESOLVED: github.com → 140.82.121.4

=== Second lookup (should be instant) ===
💨 CACHE HIT: github.com → 140.82.121.4 (age: 0.0s)

=== Add more domains ===
🌐 QUERYING DNS: google.com
✅ RESOLVED: google.com → 142.250.185.46
🌐 QUERYING DNS: stackoverflow.com
✅ RESOLVED: stackoverflow.com → 151.101.1.69

📋 Current Cache Contents:
  github.com           → 140.82.121.4    (expires in 60s)
  google.com           → 142.250.185.46  (expires in 59s)
  stackoverflow.com    → 151.101.1.69    (expires in 58s)

=== Wait 3 seconds and check again ===
💨 CACHE HIT: github.com → 140.82.121.4 (age: 3.0s)

=== Simulate 61 seconds passing ===
⏰ CACHE EXPIRED: github.com (age: 61.0s)
🌐 QUERYING DNS: github.com
✅ RESOLVED: github.com → 140.82.121.4
```

---

## 10. Going Deeper: Command-Line DNS Tools

Before writing Python code, professional developers use these built-in tools:

### `nslookup` (Available on Windows, Mac, Linux)
```bash
# Basic lookup
nslookup github.com

# Query specific DNS server
nslookup github.com 8.8.8.8

# Get MX records
nslookup -type=MX gmail.com
```

### `dig` (Mac/Linux, more powerful)
```bash
# Basic lookup
dig github.com

# Show only the answer
dig github.com +short

# Trace the full resolution path
dig github.com +trace

# Query specific record type
dig github.com AAAA
dig github.com MX
dig github.com TXT
```

### `host` (Mac/Linux, simplest)
```bash
# Quick lookup
host github.com

# Reverse lookup
host 140.82.121.4
```

**Your Task:** Try each command and compare the outputs. Which one do you find most readable?

---

## 11. Summary: What You've Learned

✅ **The DNS Hierarchy:** Root → TLD → Authoritative servers  
✅ **Record Types:** A, AAAA, CNAME, MX, NS, TXT  
✅ **Caching & TTL:** How the internet stays fast  
✅ **Security Risks:** Cache poisoning, DDoS, hijacking  
✅ **Python DNS:** Using `socket` and `dnspython` libraries  
✅ **Real-World Impact:** Why DNS outages break the internet  

**Next Time:** We'll explore **Load Balancing & Reverse Proxies** — how websites handle millions of users without crashing.

---

## 12. Challenge Questions (For Discussion)

1. **Privacy Question:** When you visit `secretwebsite.com`, your ISP's DNS server sees that request (even if you use HTTPS). How can you hide your DNS queries?
   - *Hint: Research DNS over HTTPS (DoH) and VPNs*

2. **Performance Question:** Cloudflare claims `1.1.1.1` is faster than Google's `8.8.8.8`. Run the benchmark script — is this true for you? Why might results vary?

3. **Architecture Question:** If DNS is so important, why do root servers handle millions of queries per second without crashing? 
   - *Hint: Research "anycast routing"*

4. **Business Question:** In 2014, Microsoft bought a DNS company for $100 million. Why is DNS valuable enough to cost that much?
   - *Hint: Think about data, control, and blocking*

---

**📌 Save this notebook!** Every time you type a URL, you'll now understand the invisible treasure hunt happening behind the scenes.