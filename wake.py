from voice import listen
from voice import speak
import time

# Shared state
_on_wake_callback = None
_is_paused = False

def set_wake_callback(callback):
    """Register GUI callback"""
    global _on_wake_callback
    _on_wake_callback = callback

def pause_wake_detection(state: bool):
    """Pause or resume the wake word listener to avoid mic conflicts."""
    global _is_paused
    _is_paused = state

def start_wake_listener():
    """Background thread that listens for 'alysa'."""
    print("[Wake] Wake word listener started...")

    while True:
        # If ALYSA is currently processing a command, skip listening for wake word
        if _is_paused:
            time.sleep(0.5)
            continue
            
        try:
            command = listen()

            if any(word in command for word in ["alysa", "alisa", "alisha", "elisa", "alissa", "lisa", "alexa"]):
                print("[Wake] Wake word detected!")
                # Immediately pause ourselves so the main listener can take over
                pause_wake_detection(True) 
                
                speak("Yes Anurag, how can I help you")

                if _on_wake_callback:
                    _on_wake_callback()

        except Exception as e:
            time.sleep(0.1)
            continue
