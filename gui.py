import customtkinter as ctk
import tkinter as tk
import math
import threading
import random

try:
    import pyaudio
    import audioop
    _audio_available = True
except Exception:
    _audio_available = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG        = "#050d1a"
CYAN      = "#00f5ff"
CYAN_DIM  = "#006577"
CYAN_GLOW = "#00cfdd"
GOLD      = "#ffcc00"
RED       = "#ff3333"
GREEN     = "#00ff88"

CX, CY, R = 300, 300, 140

_is_speaking = False
_status_label = None
_status_var = None

def set_speaking_state(state):
    global _is_speaking
    _is_speaking = state

def _get_speaking_state():
    """Read live state from voice module, fall back to local flag."""
    try:
        import voice
        return voice.is_speaking
    except Exception:
        return _is_speaking

def update_status(text, color="cyan"):
    if _status_var and _status_label:
        color_hex = CYAN if color == "cyan" else (GREEN if color == "green" else (RED if color == "red" else color))
        _status_label.after(0, lambda: _status_var.set(text))
        _status_label.after(0, lambda: _status_label.configure(text_color=color_hex))

mic_level = 0.0

def _mic_monitor():
    global mic_level
    if not _audio_available:
        return
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            rms = audioop.rms(data, 2)
            val = rms / 20.0
            mic_level = min(100, val)
    except Exception:
        pass

threading.Thread(target=_mic_monitor, daemon=True).start()

_app = None

def close_gui():
    """Safely destroy the tkinter window from any thread."""
    if _app is not None:
        try:
            _app.after(0, _app.destroy)
        except Exception:
            pass

def start_gui():
    global _status_label, _status_var, _app
    
    app = ctk.CTk()
    _app = app
    app.geometry("780x720")
    app.title("A.L.Y.S.A  —  AI HUD")
    app.configure(fg_color=BG)
    app.resizable(False, False)

    title_frame = ctk.CTkFrame(app, fg_color="transparent")
    title_frame.pack(pady=(18, 0))

    ctk.CTkLabel(title_frame, text="A.L.Y.S.A", font=("Courier New", 46, "bold"), text_color=CYAN).pack()
    ctk.CTkLabel(title_frame, text="Autonomous Learning & Yielding Smart Assistant", font=("Courier New", 11), text_color=CYAN_DIM).pack()

    canvas = tk.Canvas(app, width=600, height=600, bg=BG, highlightthickness=0)
    canvas.pack()

    _status_var = tk.StringVar(value="⏳  Say  'Alysa'  to activate...")
    _status_label = ctk.CTkLabel(app, textvariable=_status_var, font=("Courier New", 14), text_color=CYAN_DIM)
    _status_label.pack(pady=(0, 8))

    def draw_static_rings():
        for i, (r_offset, alpha) in enumerate([(0, CYAN_DIM), (18, "#003d4d"), (36, "#001e26")]):
            r = R + r_offset
            canvas.create_oval(CX - r, CY - r, CX + r, CY + r, outline=alpha, width=1, tags="static")
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            canvas.create_line(CX + (R - 10) * math.cos(rad), CY + (R - 10) * math.sin(rad),
                               CX + (R + 18) * math.cos(rad), CY + (R + 18) * math.sin(rad),
                               fill=CYAN_DIM, width=1, tags="static")

    draw_static_rings()

    rotate_angle = [0]
    def animate_rotate():
        canvas.delete("rotate")
        a = rotate_angle[0]
        for i in range(0, 360, 15):
            canvas.create_arc(CX - (R+36), CY - (R+36), CX + (R+36), CY + (R+36),
                              start=i + a, extent=8, outline=CYAN, width=2, style=tk.ARC, tags="rotate")
        rotate_angle[0] = (rotate_angle[0] + 2) % 360
        app.after(30, animate_rotate)

    animate_rotate()

    pulse_r = [R - 60]
    pulse_dir = [1]
    def animate_pulse():
        canvas.delete("pulse")
        r = pulse_r[0]
        speaking = _get_speaking_state()
        if speaking:
            canvas.create_oval(CX - r, CY - r, CX + r, CY + r, outline=GREEN, width=4, tags="pulse")
            pulse_dir[0] = 1 if r < R - 20 else -1
            pulse_r[0] += pulse_dir[0] * 3.0
        else:
            canvas.create_oval(CX - r, CY - r, CX + r, CY + r, outline=CYAN, width=2, tags="pulse")
            pulse_r[0] += pulse_dir[0] * 0.8
            if pulse_r[0] > R - 10 or pulse_r[0] < R - 65:
                pulse_dir[0] *= -1
        app.after(20, animate_pulse)

    animate_pulse()

    core_r = [18]
    core_dir = [1]
    def animate_core():
        canvas.delete("core")
        r = core_r[0]
        speaking = _get_speaking_state()
        base_col = GREEN if speaking else CYAN
        for layer, col in [
            (r + 14, "#003315" if speaking else "#001515"),
            (r + 8,  "#005522" if speaking else "#003333"),
            (r,      base_col)
        ]:
            canvas.create_oval(CX - layer, CY - layer, CX + layer, CY + layer, fill=col, outline="", tags="core")
        speed = 0.5 if speaking else 0.15
        core_r[0] += core_dir[0] * speed
        if core_r[0] > 26 or core_r[0] < 14:
            core_dir[0] *= -1
        app.after(30, animate_core)

    animate_core()

    # Waveform equalizer
    BAR_COUNT  = 40
    BAR_W      = 8
    BAR_GAP    = 6
    WAVE_LEFT  = 60
    WAVE_BOT   = 560
    wave_heights = [random.uniform(4, 30) for _ in range(BAR_COUNT)]
    wave_targets  = [random.uniform(4, 50) for _ in range(BAR_COUNT)]

    def animate_wave():
        canvas.delete("wave")
        speaking = _get_speaking_state()
        for i in range(BAR_COUNT):
            diff = wave_targets[i] - wave_heights[i]
            wave_heights[i] += diff * 0.3
            if abs(diff) < 2:
                if mic_level > 5:
                    wave_targets[i] = random.uniform(mic_level * 0.2, mic_level * 1.5)
                elif speaking:
                    wave_targets[i] = random.uniform(20, 60)
                else:
                    wave_targets[i] = random.uniform(2, 12)
            h = min(100, max(2, wave_heights[i]))
            x = WAVE_LEFT + i * (BAR_W + BAR_GAP)
            col = GOLD if speaking else (CYAN_GLOW if mic_level > 5 else CYAN_DIM)
            canvas.create_rectangle(x, WAVE_BOT - h, x + BAR_W, WAVE_BOT + h, fill=col, outline="", tags="wave")
        app.after(40, animate_wave)

    animate_wave()

    def draw_corners():
        sz, pad = 24, 4
        corners = [
            (pad, pad, pad + sz, pad, pad, pad + sz),
            (600 - pad, pad, 600 - pad - sz, pad, 600 - pad, pad + sz),
            (pad, 600 - pad, pad + sz, 600 - pad, pad, 600 - pad - sz),
            (600 - pad, 600 - pad, 600 - pad - sz, 600 - pad, 600 - pad, 600 - pad - sz),
        ]
        for pts in corners:
            canvas.create_line(pts[0], pts[1], pts[2], pts[3], fill=CYAN_GLOW, width=2)
            canvas.create_line(pts[0], pts[1], pts[4], pts[5], fill=CYAN_GLOW, width=2)

    draw_corners()

    app.mainloop()