# Codelab: Build Your Own AI Agent from Scratch

Welcome! In this lab, you are going to pull back the curtain on how AI actually works. You will build a fully functional AI Agent in Python, starting from a raw "brain" and upgrading it to have memory, the ability to search the internet, and even the power to control your computer.

## Prerequisites
1. Python installed on your computer.
2. Install the Google GenAI library: `pip install google-genai`
3. A free Gemini API key from [Google AI Studio](https://aistudio.google.com/).

---

## Step 1: The Goldfish (No Memory)

At its core, a Large Language Model (LLM) processes text, spits out an answer, and immediately forgets you exist. Let's prove it.

Create a file called `agent.py` and run this code:

```python
import os
from google import genai

# Initialize the AI Brain
client = genai.Client(api_key="YOUR_API_KEY_HERE")
MODEL_ID = "gemini-3-flash-preview"

print("--- DEMO 1: NO MEMORY ---")
while True:
    user_input = input("\nYou: ")
    if user_input.lower() == 'quit':
        break
        
    # We send ONLY the current message to the AI
    response = client.models.generate_content(
        model=MODEL_ID, 
        contents=user_input
    )
    print(f"AI: {response.text}")
```
**Try this:**
1. Say: *"My name is [Your Name]"*
2. Say: *"What is my name?"*
*Notice how it fails? It has no memory!*

---

## Step 2: The Parrot (Adding Memory)

To fix the memory issue, we don't change the AI. We change **our code**. We will create a list (`chat_history`) and send the *entire conversation* to the AI every single time.

Update your loop to look like this:

```python
print("--- DEMO 2: WITH MEMORY ---")
chat_history = []

while True:
    user_input = input("\nYou: ")
    if user_input.lower() == 'quit':
        break
        
    # 1. Save the user's message
    chat_history.append({"role": "user", "parts": [{"text": user_input}]})
    
    # 2. Send the ENTIRE history to the LLM
    response = client.models.generate_content(
        model=MODEL_ID, 
        contents=chat_history
    )
    
    # 3. Save the AI's response so it remembers what it said
    llm_reply = response.text
    print(f"AI: {llm_reply}")
    chat_history.append({"role": "model", "parts": [{"text": llm_reply}]})
```
**Try the name test again.** It works! Memory is just a transcript passed back and forth.

---

## Step 3: The Detective (Adding a Weather Tool)

LLMs cannot browse the internet. To give it internet access, we have to write a Python function (a "Tool") and teach the AI how to ask us to run it.

First, add this weather fetching function to the top of your file:

```python
import urllib.request
import urllib.parse
import json

def get_weather(city):
    print(f"\n[🌡️ AGENT ACTION: Checking weather for '{city}'...]")
    try:
        safe_city = urllib.parse.quote(city.strip())
        url = f"https://wttr.in/{safe_city}?format=j1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Python Agent/1.0'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            temp_c = data['current_condition'][0]['temp_C']
            desc = data['current_condition'][0]['weatherDesc'][0]['value']
            return f"Weather in {city}: {desc}, {temp_c}°C."
    except Exception as e:
        return "Weather search failed."
```

Now, update your loop to teach the AI a secret command (`WEATHER:`):

```python
print("--- DEMO 3: ADDING A TOOL ---")
chat_history = []

# Secret Instructions for the AI
system_rules = "If the user asks for the weather, reply EXACTLY with: 'WEATHER: [city]'. Do not say anything else."
chat_history.append({"role": "user", "parts": [{"text": system_rules}]})
chat_history.append({"role": "model", "parts": [{"text": "Understood."}]})

while True:
    user_input = input("\nYou: ")
    if user_input.lower() == 'quit': break
        
    chat_history.append({"role": "user", "parts": [{"text": user_input}]})
    response = client.models.generate_content(model=MODEL_ID, contents=chat_history)
    llm_reply = response.text
    
    # THE INTERCEPT: Did the AI ask to use our tool?
    if "WEATHER:" in llm_reply:
        city = llm_reply.replace("WEATHER:", "").strip()
        weather_data = get_weather(city)
        
        # Save the attempt, and feed the data back to the AI
        chat_history.append({"role": "model", "parts": [{"text": llm_reply}]})
        chat_history.append({"role": "user", "parts": [{"text": f"Search Results: {weather_data}. Now answer my original question naturally. Do not use the WEATHER command again."}]})
        
        # Ask the AI to formulate the final sentence
        response = client.models.generate_content(model=MODEL_ID, contents=chat_history)
        llm_reply = response.text

    print(f"AI: {llm_reply}")
    chat_history.append({"role": "model", "parts": [{"text": llm_reply}]})
```
**Try asking:** *"What is the weather in Tokyo?"* Watch the agent pause, fetch the data, and summarize it for you!

---

## Step 4: The Personal Assistant (Local Actions)

Fetching the weather is cool, but real AI Agents can take *actions*. Let's give your AI the ability to read and write physical files on your hard drive. 

Add these two functions to the top of your script:

```python
def add_todo(task):
    print(f"\n[💾 AGENT ACTION: Saving '{task}' to local todo.txt...]")
    with open("todo.txt", "a") as f:
        f.write(task + "\n")
    return f"Success! Added '{task}' to your to-do list."

def read_todos():
    print(f"\n[📂 AGENT ACTION: Reading local todo.txt...]")
    if not os.path.exists("todo.txt"):
        return "Your to-do list is empty."
    with open("todo.txt", "r") as f:
        tasks = f.read()
    return f"Here are your current tasks:\n{tasks}"
```

**Your Challenge:** 
Create a new demo loop. Change the `system_rules` to tell the AI it has two new commands: `ADD_TODO: [task]` and `READ_TODOS`. Set up your `if/elif` intercept block to catch these commands and run the correct Python functions. 

*Try telling it: "I need to do my math homework tonight." Then, check your computer's folder—did the AI create a real text file?*

---

## Step 5: The Polymath (Adding Wikipedia)

Now let's give it the ultimate knowledge tool. Add this function to your file:

```python
import re

def get_wikipedia(query):
    print(f"\n[🔍 AGENT ACTION: Searching Wikipedia for '{query}'...]")
    try:
        safe_query = urllib.parse.quote(query)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_query}&utf8=&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Python Agent/1.0'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            snippet = data['query']['search'][0]['snippet']
            clean_snippet = re.sub('<[^<]+>', '', snippet) # Remove HTML tags
            return f"Wikipedia says: {clean_snippet}"
    except Exception as e:
        return "Wikipedia search failed."
```

**Your final challenge:** 
Modify the `system_rules` and your intercept block to handle `WIKIPEDIA: [topic]`. You now have a multi-tool Agent that can fetch the weather, edit your local files, AND read Wikipedia!

---

## Step 6: Going Off the Grid (Local AI with Ollama)

Up until now, every time you asked a question, your computer sent your data to Google's billion-dollar data centers to do the math. 

But what if you want privacy? What if you don't have internet? **You can run the AI brain directly on your own laptop's hardware.** 

To do this, we use a free tool called **Ollama**. Ollama runs a tiny, invisible server on your computer that mimics the industry-standard "OpenAI" format.

### The Setup:
1. Go to [ollama.com](https://ollama.com) and install the app.
2. Open your computer's Terminal (or Command Prompt) and type: `ollama run llama3.2`
   *(This will download Meta's open-source Llama model to your hard drive. It might take a few minutes!)*
3. Open a new Terminal and install the OpenAI Python library: `pip install openai`

### The Code:
Create a new file called `local_agent.py`. Notice how we point the URL to `localhost` (your own computer) instead of the internet! Also notice that the memory format changes slightly from `parts` to `content`.

```python
from openai import OpenAI

# 1. Point the client to YOUR computer! No internet required.
client = OpenAI(
    base_url="http://localhost:11434/v1", 
    api_key="my-local-key" # Not a real key, just required by the library
)

# We are now using Meta's Llama model running on your hardware
MODEL_ID = "llama3.2" 

print("--- DEMO 6: LOCAL AI ---")
print("Try turning off your Wi-Fi! It will still work.")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() == 'quit':
        break
        
    # The OpenAI format uses 'content' instead of 'parts'
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": user_input}]
    )
    
    print(f"AI: {response.choices[0].message.content}")
```

**Your Ultimate Challenge:** Can you take the Memory and Tool loops from the earlier steps and rewrite them to work with this Local AI format? 
*(Hint: You just need to change `{"role": "user", "parts": [{"text": ...}]}` to `{"role": "user", "content": ...}`)* 

Welcome to the future of open-source AI!