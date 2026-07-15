"""
Speak & Recognize
------------------
A simple desktop Speech Recognition app built with:
  - pygame              -> the GUI (window, button, text rendering)
  - SpeechRecognition   -> converts your microphone audio into text
                            (uses Google's free Web Speech API under the hood)
  - PyAudio             -> lets SpeechRecognition capture audio from the mic
  - pandas              -> stores every recognized phrase (with a timestamp)
                            in a CSV log file, so the app "remembers" history
  - os                  -> checks whether the log file already exists
  - threading           -> runs the microphone listening in the background so
                            the pygame window never freezes while you talk

How it works, in one sentence:
    Click the button -> app records your voice for a few seconds ->
    sends the audio to Google's speech API -> gets back text ->
    shows it on screen and appends it to history.csv
"""

import os
import sys
import threading
from datetime import datetime

import pygame
import pandas as pd
import speech_recognition as sr

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------
WIDTH, HEIGHT = 600, 650
BG_COLOR = (24, 24, 28)
PANEL_COLOR = (36, 36, 42)
ACCENT = (88, 166, 255)
ACCENT_DARK = (58, 110, 175)
TEXT_COLOR = (235, 235, 235)
MUTED_COLOR = (150, 150, 155)
ERROR_COLOR = (255, 100, 100)
LOG_FILE = "history.csv"

# --------------------------------------------------------------------------
# APP STATE
# --------------------------------------------------------------------------
class AppState:
    """Small container so the background thread and the main loop can
    share data safely without global variables scattered everywhere."""
    def __init__(self):
        self.status = "idle"          # idle | listening | processing | done | error
        self.result_text = "Click the button and start speaking."
        self.history = []             # list of (timestamp, text) for on-screen display
        self.lock = threading.Lock()  # protects status/result_text across threads

    def set(self, status, text=None):
        with self.lock:
            self.status = status
            if text is not None:
                self.result_text = text

    def get(self):
        with self.lock:
            return self.status, self.result_text


state = AppState()
recognizer = sr.Recognizer()


# --------------------------------------------------------------------------
# LOGGING (pandas + os)
# --------------------------------------------------------------------------
def load_history():
    """Load past recognized phrases from CSV into memory (if the file exists)."""
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        return list(df[["timestamp", "text"]].itertuples(index=False, name=None))
    return []


def append_history(text):
    """Append one new recognized phrase to the CSV log using pandas."""
    row = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": text,
    }])
    header_needed = not os.path.exists(LOG_FILE)
    row.to_csv(LOG_FILE, mode="a", header=header_needed, index=False)
    return row.iloc[0]["timestamp"], text


# --------------------------------------------------------------------------
# SPEECH RECOGNITION (runs in a background thread)
# --------------------------------------------------------------------------
def listen_and_recognize():
    """
    Captures a few seconds of audio from the default microphone and asks
    Google's free speech-recognition API to transcribe it.
    Runs on a separate thread so the pygame window keeps redrawing smoothly.
    """
    try:
        state.set("listening", "Listening... speak now")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

        state.set("processing", "Processing what you said...")
        text = recognizer.recognize_google(audio)

        timestamp, text = append_history(text)
        with state.lock:
            state.history.insert(0, (timestamp, text))
        state.set("done", text)

    except sr.WaitTimeoutError:
        state.set("error", "No speech detected. Try again.")
    except sr.UnknownValueError:
        state.set("error", "Couldn't understand that. Try again.")
    except sr.RequestError:
        state.set("error", "No internet / API unavailable.")
    except OSError:
        state.set("error", "No microphone found.")
    except Exception as e:
        state.set("error", f"Unexpected error: {e}")


def start_listening_thread():
    status, _ = state.get()
    if status in ("listening", "processing"):
        return  # already busy, ignore extra clicks
    threading.Thread(target=listen_and_recognize, daemon=True).start()


# --------------------------------------------------------------------------
# UI HELPERS
# --------------------------------------------------------------------------
def draw_button(screen, rect, label, font, hovered):
    color = ACCENT if hovered else ACCENT_DARK
    pygame.draw.rect(screen, color, rect, border_radius=14)
    text_surf = font.render(label, True, (15, 15, 20))
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


def wrap_text(text, font, max_width):
    """Simple word-wrap so long sentences don't run off the window."""
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# --------------------------------------------------------------------------
# MAIN APP
# --------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Speak & Recognize")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 42, bold=True)
    body_font = pygame.font.SysFont(None, 26)
    small_font = pygame.font.SysFont(None, 20)
    button_font = pygame.font.SysFont(None, 30, bold=True)

    state.history = load_history()[::-1][:8]  # most recent 8 entries, newest first

    button_rect = pygame.Rect(0, 0, 260, 64)
    button_rect.center = (WIDTH // 2, 220)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        hovered = button_rect.collidepoint(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hovered:
                    start_listening_thread()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                start_listening_thread()

        status, result_text = state.get()

        # ---------------- draw ----------------
        screen.fill(BG_COLOR)

        title = title_font.render("Speak & Recognize", True, TEXT_COLOR)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 60)))

        subtitle = small_font.render(
            "Click the button (or press SPACE) and speak into your mic",
            True, MUTED_COLOR,
        )
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 100)))

        label = {
            "idle": "Click to Speak",
            "listening": "Listening...",
            "processing": "Processing...",
            "done": "Click to Speak Again",
            "error": "Try Again",
        }.get(status, "Click to Speak")
        draw_button(screen, button_rect, label, button_font, hovered)

        # status dot
        dot_color = {
            "idle": MUTED_COLOR,
            "listening": ACCENT,
            "processing": (255, 200, 80),
            "done": (100, 220, 130),
            "error": ERROR_COLOR,
        }.get(status, MUTED_COLOR)
        pygame.draw.circle(screen, dot_color, (WIDTH // 2 - 150, 305), 6)
        status_label = small_font.render(status.upper(), True, dot_color)
        screen.blit(status_label, (WIDTH // 2 - 135, 297))

        # result panel
        panel_rect = pygame.Rect(40, 330, WIDTH - 80, 100)
        pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=12)
        text_color = ERROR_COLOR if status == "error" else TEXT_COLOR
        for i, line in enumerate(wrap_text(result_text, body_font, panel_rect.width - 30)):
            line_surf = body_font.render(line, True, text_color)
            screen.blit(line_surf, (panel_rect.x + 15, panel_rect.y + 15 + i * 28))

        # history panel
        hist_title = body_font.render("Recent history", True, MUTED_COLOR)
        screen.blit(hist_title, (40, 450))
        with state.lock:
            history_snapshot = list(state.history)
        for i, (timestamp, text) in enumerate(history_snapshot[:6]):
            y = 485 + i * 24
            line = f"[{timestamp}]  {text}"
            if body_font.size(line)[0] > WIDTH - 80:
                line = line[:70] + "..."
            line_surf = small_font.render(line, True, MUTED_COLOR)
            screen.blit(line_surf, (40, y))

        pygame.display.update()
        clock.tick(30)


if __name__ == "__main__":
    main()

