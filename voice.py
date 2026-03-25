import asyncio
import edge_tts
import uuid
import os
import time
import threading
import queue
import pygame
import speech_recognition as sr
import re

# Voice selection based on language detection
VOICE_HINDI = "hi-IN-SwaraNeural"
VOICE_ENGLISH = "en-US-AvaNeural"

is_speaking = False

pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

_tts_loop = asyncio.new_event_loop()
threading.Thread(target=_tts_loop.run_forever, daemon=True).start()

_speak_queue = queue.Queue()
_interrupt = threading.Event()


def interrupt():
    _interrupt.set()
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    while not _speak_queue.empty():
        try:
            _, done_event = _speak_queue.get_nowait()
            if done_event:
                done_event.set()
            _speak_queue.task_done()
        except queue.Empty:
            break


def detect_language(text):
    """Detect if text contains Hindi characters (Devanagari script)."""
    hindi_pattern = re.compile(r'[\u0900-\u097F]')
    return "hindi" if hindi_pattern.search(text) else "english"


async def _tts_generate(text, filename):
    lang = detect_language(text)
    voice = VOICE_HINDI if lang == "hindi" else VOICE_ENGLISH
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)


def _speak_worker():
    global is_speaking
    while True:
        text, done_event = _speak_queue.get()
        filename = f"voice_{uuid.uuid4().hex}.mp3"
        _interrupt.clear()
        try:
            future = asyncio.run_coroutine_threadsafe(
                _tts_generate(text, filename), _tts_loop
            )
            future.result(timeout=15)

            if _interrupt.is_set():
                return

            is_speaking = True

            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if _interrupt.is_set():
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.05)

            try:
                pygame.mixer.music.unload()
            except AttributeError:
                pass

        except Exception as e:
            print(f"[speak_worker] Error: {e}")
        finally:
            is_speaking = False
            for _ in range(5):
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                    break
                except Exception:
                    time.sleep(0.1)
            if done_event:
                done_event.set()
            _speak_queue.task_done()


threading.Thread(target=_speak_worker, daemon=True).start()


def speak(text, block=True):
    """Thread-safe TTS with automatic language detection."""
    done_event = threading.Event() if block else None
    _speak_queue.put((text, done_event))
    if block and done_event:
        done_event.wait()


def listen():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("[Mic] Listening...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                print("[Warning] No sound detected.")
                return ""
    except OSError:
        print("[Error] Microphone unavailable.")
        return ""

    try:
        # Try ENGLISH FIRST (en-US for better accuracy)
        command = r.recognize_google(audio, language='en-US')
        print(f"--> You said: '{command}'")
        return command.lower()
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print(f"[Error] Speech recognition: {e}")
        return ""