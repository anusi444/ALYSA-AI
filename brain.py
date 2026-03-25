import datetime
import webbrowser
import requests
import os
import threading
import time
import urllib.parse
import sys
from dotenv import load_dotenv
from google import genai
import voice as _voice
from voice import speak, interrupt
from memory import save_memory, get_all_memories
import gui

# Ensure UTF-8 encoding for bilingual output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1alpha'}
)

MODEL = "gemini-2.0-flash"

# Bilingual system instruction
SYSTEM_INSTRUCTION = """You are ALYSA, a helpful AI assistant.
You must respond in the SAME language the user uses.
- If the user speaks in English, respond in English.
- If the user speaks in Hindi or Hinglish, respond in Hindi (Devanagari script).
Keep responses concise and natural for real-time voice interaction."""

shutdown_flag = threading.Event()


def ai_speak(text):
    if not text:
        return
    try:
        gui.set_speaking_state(True)
    except Exception:
        pass
    speak(text)
    try:
        gui.set_speaking_state(False)
    except Exception:
        pass


def _stream_and_speak(prompt):
    """Streams response and speaks sentence by sentence in detected language."""
    buffer = ""
    sentence_endings = {'.', '?', '!', '।'}
    try:
        response = client.models.generate_content_stream(
            model=MODEL,
            contents=[
                {"role": "user", "parts": [{"text": SYSTEM_INSTRUCTION}]},
                {"role": "model", "parts": [{"text": "Understood. I will respond in the same language as the user."}]},
                {"role": "user", "parts": [{"text": prompt}]}
            ]
        )
        
        for chunk in response:
            if chunk.text:
                print(chunk.text, end='', flush=True)
                buffer += chunk.text
                
                while True:
                    idx = -1
                    for i, ch in enumerate(buffer):
                        if ch in sentence_endings:
                            idx = i
                            break
                    if idx == -1:
                        break
                    sentence = buffer[:idx + 1].strip()
                    buffer = buffer[idx + 1:]
                    if sentence:
                        sentence = sentence.replace("*", "").replace("#", "")
                        ai_speak(sentence)
        
        print()
        if buffer.strip():
            ai_speak(buffer.strip().replace("*", "").replace("#", ""))
            
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("[AI] Cooling down — rate limit hit. Waiting 15 seconds...")
            ai_speak("I need a moment to cool down.")
            time.sleep(15)
        else:
            print(f"[AI Error] {type(e).__name__}: {e}")
            ai_speak("I am having trouble connecting to my AI system.")


def ai_chat(prompt):
    memories = get_all_memories()
    mem_str = ", ".join([f"{k}: {v}" for k, v in memories.items()]) if memories else "None"
    full_prompt = f"User memory: {mem_str}\nUser: {prompt}"
    t = threading.Thread(target=_stream_and_speak, args=(full_prompt,), daemon=True)
    t.start()


def process_memory(cmd):
    if "what do you know about me" in cmd or "मेरे बारे में" in cmd:
        data = get_all_memories()
        if not data:
            ai_speak("I don't know much about you yet.")
        else:
            ai_speak("I remember: " + ", ".join(str(v) for v in data.values()))
        return True
    if "remember" in cmd or "याद रख" in cmd:
        val = cmd.replace("remember", "").replace("याद रख", "").strip()
        if not val:
            ai_speak("What would you like me to remember?")
            return True
        if "my name is" in cmd or "मेरा नाम" in cmd:
            name = cmd.split("my name is")[-1].split("मेरा नाम")[-1].strip()
            save_memory("name", name)
            ai_speak(f"I will remember your name is {name}")
        else:
            save_memory(f"mem_{int(datetime.datetime.now().timestamp())}", val)
            ai_speak("Saved to memory.")
        return True
    return False


def search(query):
    clean = query.replace("search", "").replace("खोज", "").strip()
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(clean)}")
    ai_chat(f"Give a very brief summary about {clean}")


def weather():
    try:
        key = os.getenv("WEATHER_API_KEY", "")
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Kolkata&appid={key}&units=metric"
        res = requests.get(url)
        data = res.json()
        if res.status_code == 200:
            ai_speak(f"In Kolkata, it is {data['main']['temp']} degrees with {data['weather'][0]['description']}.")
        else:
            ai_speak("I couldn't fetch the weather right now.")
    except Exception as e:
        print("Weather Error:", e)
        ai_speak("Unable to fetch weather.")


def process_command(command):
    if not command:
        return
    cmd = command.lower().strip()
    try:
        gui.update_status(f"You said: {command}", "green")
    except Exception:
        pass
    try:
        if _voice.is_speaking:
            interrupt()
    except Exception:
        pass

    if any(x in cmd for x in ["shutdown yourself", "exit program", "quit", "close alysa", "बंद करो", "शटडाउन"]):
        ai_speak("Shutting down. Goodbye!")
        shutdown_flag.set()
        return
    if process_memory(cmd):
        return
    if "time" in cmd or "समय" in cmd:
        ai_speak(f"The time is {datetime.datetime.now().strftime('%I:%M %p')}")
    elif "open youtube" in cmd or "यूट्यूब खोलो" in cmd:
        ai_speak("Opening YouTube")
        webbrowser.open("https://youtube.com")
    elif "open google" in cmd or "गूगल खोलो" in cmd:
        ai_speak("Opening Google")
        webbrowser.open("https://google.com")
    elif "search" in cmd or "latest" in cmd or "खोज" in cmd:
        search(cmd)
    elif "weather" in cmd or "मौसम" in cmd:
        weather()
    elif "open notepad" in cmd or "नोटपैड खोलो" in cmd:
        ai_speak("Opening Notepad")
        os.startfile("notepad.exe")
    elif "who are you" in cmd or "तुम कौन हो" in cmd:
        ai_speak("I am ALYSA, your AI assistant.")
    else:
        ai_chat(command)