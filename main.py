import threading
import time
from voice import listen, speak, interrupt
from brain import process_command, shutdown_flag
from gui import start_gui, update_status, close_gui
import voice as _voice

WAKE_WORDS = ["alysa", "alisa", "alisha", "alexa", "alex"]
SLEEP_WORDS = ["stop", "sleep"]


def run_alysa():
    print("🔥 ALYSA THREAD STARTED")

    active = False
    time.sleep(2)

    try:
        update_status("⏳ Say 'Alysa' to activate...", "cyan")
    except:
        pass

    while not shutdown_flag.is_set():
        try:
            print("🎤 Listening...")

            command = listen()

            if not command:
                continue

            if _voice.is_speaking:
                interrupt()

            if not active:
                if any(word in command for word in WAKE_WORDS):
                    active = True
                    update_status("🟢 Active", "green")
                    speak("Yes, I am listening")
            else:
                if any(word in command for word in SLEEP_WORDS):
                    active = False
                    update_status("⏳ Sleep mode", "cyan")
                    speak("Going to sleep")
                else:
                    process_command(command)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(1)

    # Shutdown sequence
    interrupt()
    close_gui()
    print("[ALYSA] Shutdown complete.")


def main():
    # Start voice thread FIRST
    t = threading.Thread(target=run_alysa)
    t.daemon = True
    t.start()

    # Start GUI in main thread
    start_gui()


if __name__ == "__main__":
    main()