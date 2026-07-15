# Console — Voice Transcriber (Web Version)

A browser-based speech-to-text app: a single `index.html` file, no server,
no Python install required. This is the GitHub-Pages-friendly counterpart
to the pygame desktop app.

## Deploy it on GitHub Pages (2 minutes)

1. Push this folder (just `index.html`) to a GitHub repo.
2. Go to **Settings → Pages** in that repo.
3. Under "Build and deployment", set **Source: Deploy from a branch**,
   branch: `main`, folder: `/ (root)` → **Save**.
4. GitHub gives you a live URL like
   `https://<your-username>.github.io/<repo-name>/` within a minute or two.

That link works for anyone, on any device, in Chrome or Edge — no install
step for them at all. This is the version you can actually put a live demo
link for in your resume, unlike the pygame app which requires someone to
clone it and have Python + a mic set up locally.

## How it works (interview-ready explanation)

**1. Speech recognition — the browser's built-in Web Speech API**
Instead of `SpeechRecognition` + `PyAudio` (Python libraries that talk to
your OS's microphone), this version uses `window.SpeechRecognition` /
`window.webkitSpeechRecognition` — an API built directly into Chrome and
Edge. The browser itself captures microphone audio, sends it off for
recognition, and fires an `onresult` event with the transcribed text. There's
no server-side code at all; everything happens client-side in JavaScript.
This is *why* it only works in Chromium-based browsers (Chrome, Edge) —
Firefox and Safari haven't implemented this API.

**2. No backend, no build step**
It's one static HTML file with inlined CSS and JavaScript. That's what makes
GitHub Pages a fit: Pages only serves static files, it can't run a Python
process. If you wanted to keep the exact pygame/PyAudio/Google-API version
alive online, you'd need a real server (e.g. a small Flask backend on
Render/Railway) — GitHub Pages alone can't host that.

**3. Persisting history — `localStorage` instead of `pandas`/CSV**
The Python version wrote rows to `history.csv` with `pandas`. A static
webpage has no filesystem to write to, so this version uses the browser's
`localStorage` — a simple built-in key/value store scoped to your browser.
History persists across page reloads on the same device/browser, but (unlike
a server-side file) it's private to that one browser and isn't shared
between devices.

**4. The waveform / status console**
Purely a UI touch: while listening, a row of bars animates with random
heights to suggest a live audio signal (like a studio VU meter), and settles
back to a flat line when idle. It's `requestAnimationFrame` randomizing bar
heights — not an analysis of the actual audio signal.

## Limitations worth knowing (good interview material)

- **Browser support**: Chrome/Edge only. The page detects this and shows a
  clear message if opened in an unsupported browser.
- **Needs internet**: like the Python version's Google API call, the
  browser's speech engine typically needs a network connection.
- **Privacy note**: audio is sent to the browser vendor's speech service
  (e.g. Google's, in Chrome) for transcription — same trust boundary as the
  Python version's `recognize_google()` call.
- **Not the same as speaker recognition**: this still only answers "what was
  said," not "who said it."

## Relationship to the Python (pygame) version

| | Python / pygame app | Web version |
|---|---|---|
| Runs | Locally, needs Python + PyAudio installed | Anywhere, in a supported browser |
| Mic access | `PyAudio` | Browser's Web Speech API |
| Recognition engine | `speech_recognition.recognize_google()` | Browser's built-in engine |
| History storage | `pandas` → `history.csv` | `localStorage` |
| Shareable as a live link | No | Yes — GitHub Pages |

Keep both in your resume if you like: the Python one shows you can work with
threading, hardware I/O, and pandas; the web one shows you can ship
something people can actually click on without installing anything.
