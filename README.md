# Speak & Recognize — Speech Recognition Desktop App

A small Python desktop app that listens to your microphone, converts your
speech to text, and keeps a running history — built with `pygame`,
`SpeechRecognition`, `PyAudio`, `pandas`, and `os`.

## Run it

```bash
pip install -r requirements.txt
python speech_recognition_app.py
```

On Windows, `PyAudio` sometimes needs a prebuilt wheel:
`pip install pipwin && pipwin install pyaudio`

Click the button (or press SPACE), speak for a few seconds, and the
recognized text appears on screen and gets saved to `history.csv`.

## How it works (interview-ready explanation)

**1. The GUI layer — `pygame`**
`pygame` draws the window, the "Click to Speak" button, the colored status
dot, and the text panels. The `while True` loop is pygame's standard
pattern: handle events (clicks, quitting) → clear the screen → redraw
everything → flip the display → repeat, ~30 times a second (`clock.tick(30)`).

**2. Not freezing while listening — `threading`**
Capturing audio and waiting for a network response can take a few seconds.
If that happened directly inside the pygame loop, the window would freeze
and look crashed. So clicking the button spins up a background
`threading.Thread` that does the microphone/recognition work, while the
main loop keeps redrawing at full speed. The two threads share a small
`AppState` object protected by a `threading.Lock`, so there's no race
condition when the UI thread reads `status`/`result_text` while the
background thread is writing them.

**3. Turning sound into text — `SpeechRecognition` + `PyAudio`**
- `PyAudio` is the low-level library that actually talks to your
  microphone hardware and gives Python raw audio.
- `speech_recognition` (`sr`) wraps that audio and sends it to a speech-to-text
  engine. This app uses `recognizer.recognize_google(audio)`, which calls
  Google's free Web Speech API and returns the transcribed text (this needs
  an internet connection; that's why there's a `except sr.RequestError`
  branch for "no internet").
- `recognizer.adjust_for_ambient_noise()` briefly samples background noise
  first so quiet rooms/loud rooms both work reasonably well.
- `recognizer.listen(..., timeout=5, phrase_time_limit=8)` waits up to 5s
  for you to start talking, then records up to 8s of speech.

**4. Remembering what was said — `pandas` + `os`**
Every successful recognition is appended as a row (`timestamp`, `text`) to
`history.csv` using `pandas.DataFrame.to_csv(..., mode="a")`. `os.path.exists()`
checks whether the file already exists, so the header row is only written
once. On startup, `pd.read_csv()` reloads that file so your history persists
between runs — this is a simple example of *persisting application state to
disk*.

**5. Error handling**
The app distinguishes between a few real-world failure modes and shows a
readable message for each:
- `WaitTimeoutError` — you didn't say anything in time
- `UnknownValueError` — audio was captured but couldn't be transcribed
- `RequestError` — no internet / API problem
- `OSError` — no microphone detected

## Possible extensions (good talking points for an interview)

- Swap `recognize_google` for an offline engine (e.g. `Vosk` or `whisper`)
  so it works without internet.
- Add speaker identification (matching a voice to a known person) using a
  library like `resemblyzer` or `pyannote.audio` — this is what
  distinguishes "speech recognition" (what was said) from "speaker
  recognition" (who said it).
- Package it with `pyinstaller` into a standalone `.exe`/binary.
- Add a settings panel to change the recognition language.
