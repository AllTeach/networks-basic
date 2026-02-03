# Teacher Notes: NAT, IPv4 Exhaustion, and Tunneling

**Topic:** Networking Basics — Session 4  
**Duration:** 45-60 Minutes  
**Goal:** Students will understand why their local server isn't globally accessible, learn about the IPv4 shortage, and use tunneling to bypass NAT.

---

## ⏳ Lesson Flow & Timeline

| Time | Activity | Key Concept |
| :--- | :--- | :--- |
| **00-05** | **The Hook:** "The Localhost Trap" | Why can't I see your screen? |
| **05-15** | **Concept:** IPv4 & The Address Shortage | The "Apartment Building" Analogy. |
| **15-25** | **Coding:** Private vs. Public IP | Running the Python scripts. |
| **25-35** | **Concept:** NAT (The Translator) | How the router lies to the internet. |
| **35-55** | **Lab:** Tunnels with `ngrok` | Bypassing the router safely. |
| **55-60** | **Wrap Up:** Discussion | Security implications. |

---

## 1. The Hook (5 mins)
*   **Action:** Have students run their server from the previous lesson (`http_server.py`).
*   **Challenge:** Ask them to paste their link (`http://localhost:8080`) into the chat and try to click someone else's.
*   **Expected Result:** "It doesn't work!" or "It just opens *my* own server!"
*   **Discussion:** "You are all shouting 'Room 101' into a walkie-talkie. Everyone goes to *their own* Room 101. We need a unique address."

---

## 2. The Theory: IPv4 Exhaustion (10 mins)
*   **The Problem:**
    *   IPv4 has ~4.3 billion addresses ($2^{32}$).
    *   We have 8+ billion people and 30+ billion devices.
    *   *Question:* "How does everyone get online if we ran out of numbers in 2011?"
*   **The Analogy (Apartment Building):**
    *   **Public IP:** The street address of the building (limited supply, expensive).
    *   **Private IP:** The apartment number (infinite supply, because every building can reuse 'Apt 101').
    *   **NAT (Router):** The doorman who receives all mail for the building and walks it to the correct apartment.

---

## 3. The Code: Seeing the Difference (10 mins)
*   **Activity:** Run the scripts from the tutorial.
*   **Expected "Aha!" Moment:**
    *   Students verify their **Local IP** is different from their **Public IP**.
    *   **Crucial Step:** Ask two students in the same room (or on the same school WiFi) to read out their *Public* IP.
    *   *Result:* They will be identical. This proves they are sharing one connection!

---

## 4. Deep Dive: NAT (Network Address Translation) (10 mins)
*   **Explain:** The router keeps a "Translation Table."
    *   *Internal:* `192.168.1.5:54321` -> *External:* `85.203.11.22:10001`
*   **The Limitation:**
    *   NAT is great for *outgoing* calls (you calling Google).
    *   NAT is terrible for *incoming* calls (your friend calling your server).
    *   *Why?* The router receives a packet for port 8080. It looks at its list. Nobody initiated a call on port 8080. **It drops the packet.**

---

## 5. The Solution: Tunneling (Lab) (20 mins)
*   **Why not Port Forwarding?**
    *   Security risk (leaving a door open).
    *   Impossible on School WiFi or Mobile networks (Carrier-Grade NAT).
*   **Ngrok Explanation:**
    *   Ngrok is a "reverse tunnel."
    *   Instead of waiting for a call (which NAT blocks), your laptop *makes* an outgoing call to Ngrok's cloud.
    *   Ngrok accepts traffic from the public internet and pushes it down that open line.
*   **Troubleshooting:**
    *   *Windows Firewall:* May pop up asking for permission. Click "Allow".
    *   *Authtoken:* Ensure they copy the token correctly without spaces.

---

## 6. Wrap Up Discussion (5 mins)
*   **Q:** "Why did the logs show the visitor IP as `127.0.0.1`?"
    *   **A:** Because the request technically came from the `ngrok` app running *on the same computer*.
*   **Future Tease:** "What if we didn't need NAT? What if every grain of sand could have an IP?" -> **IPv6**.