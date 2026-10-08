#!/usr/bin/env python3
"""Free AI bridge: lets Open WebUI use Rabbid's own free tools through OpenAI-style endpoints. 127.0.0.1:8898 only.

  POST /v1/audio/speech        -> Kokoro voice (bm_george, the British butler voice)   [Open WebUI "Text-to-Speech"]
  POST /v1/images/generations  -> FastSD CPU via `imagine`                             [Open WebUI "Image Generation"]
  POST /v1/chat/completions    -> model "auto": picks the best free brain for the message and passes it to the brain
                                  switch (127.0.0.1:4000), streaming included        [Open WebUI "🤖 Auto"]

Runs with the Kokoro venv (~/.local/share/kokoro/venv). The voice loads on first use and is dropped after
10 idle minutes; pictures run as a separate `imagine` process, so nothing big sits in memory (15 GB laptop).
"""
import base64, io, json, os, re, subprocess, tempfile, threading, time, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import soundfile as sf

KOKORO_DIR = os.path.expanduser("~/.local/share/kokoro")
IMAGINE = os.path.expanduser("~/.local/bin/imagine")
IDLE_UNLOAD = 600
_kokoro, _last_used, _lock, _img_lock = None, 0.0, threading.Lock(), threading.Lock()


def speech(text, voice="bm_george", speed=1.0):
    global _kokoro, _last_used
    with _lock:
        if _kokoro is None:
            from kokoro_onnx import Kokoro
            _kokoro = Kokoro(f"{KOKORO_DIR}/kokoro-v1.0.onnx", f"{KOKORO_DIR}/voices-v1.0.bin")
        _last_used = time.time()
        if not voice or voice in ("alloy", "echo", "fable", "onyx", "nova", "shimmer"):  # OpenAI names -> Rabbid's voice
            voice = "bm_george"
        text = re.sub(r"[*_#`>|]", "", text)  # don't read markdown symbols aloud
        audio, rate = _kokoro.create(text[:4000], voice=voice, speed=speed, lang="en-gb" if voice[0] == "b" else "en-us")
    buf = io.BytesIO()
    sf.write(buf, audio, rate, format="WAV")
    return buf.getvalue()


def unloader():
    global _kokoro
    while True:
        time.sleep(60)
        with _lock:
            if _kokoro is not None and time.time() - _last_used > IDLE_UNLOAD:
                _kokoro = None


SWITCH = "http://127.0.0.1:4000/v1/chat/completions"
CODE_WORDS = ("code", "script", "python", "bash", "javascript", "html", "css", "sql", "regex", "function", "error",
              "bug", "debug", "compile", "terminal", "command", "linux", "docker", "git ", "json", "yaml", "config",
              "install", "traceback", "stack trace", "```")
SMART_WORDS = ("think hard", "step by step", "plan ", "planning", "compare", "analy", "pros and cons", "should i",
               "decide", "strategy", "why does", "why do", "explain why", "prove", "reason", "best way to", "trade-off")

# 2026-10-08: a fast free AI reads the question and picks the lane (word lists sent "should I install Steam?" to the
# coder). Groq gpt-oss-20b: ~0.3 s, 10/10 on the test questions. Up to 3 s, then the word lists decide.
PICKER = "https://api.groq.com/openai/v1/chat/completions"
PICKER_PROMPT = (
    "Sort the user's newest message into ONE lane. Reply with only the lane word.\n"
    "coder = writing, fixing or explaining code, scripts, terminal commands, config files, error messages, "
    "installing or setting up software\n"
    "smart = needs careful reasoning: decisions, comparisons, plans, pros and cons, math or logic problems, "
    "'why' questions that need a real explanation, advice with trade-offs\n"
    "chat = everything else: facts, quick questions, small talk, stories, jokes, definitions, recommendations")


def groq_key():
    try:
        for line in open(os.path.expanduser("~/.config/crew/ai-keys.env")):
            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"\'')
    except OSError:
        pass
    return ""


def ask_picker(messages, content):
    """Ask the fast free AI for the lane; None if it can't answer in time."""
    import urllib.request
    key = groq_key()
    if not key:
        return None
    # A little of the conversation so short follow-ups ("ok do it") land in the same lane
    before = [m for m in messages[:-1] if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)][-2:]
    context = "".join(f"[earlier {m['role']}]: {m['content'][:400]}\n" for m in before)
    body = {"model": "openai/gpt-oss-20b", "temperature": 0, "reasoning_effort": "low", "max_completion_tokens": 200,
            "messages": [{"role": "system", "content": PICKER_PROMPT},
                         {"role": "user", "content": f"{context}[newest message]: {content[:2000]}"}]}
    req = urllib.request.Request(PICKER, json.dumps(body).encode(), {"Content-Type": "application/json",
                                 "Authorization": f"Bearer {key}", "User-Agent": "curl/8"})  # Groq 403s Python's UA
    try:
        word = json.load(urllib.request.urlopen(req, timeout=3))["choices"][0]["message"]["content"].strip().lower()
    except Exception:
        return None
    for lane in ("coder", "smart", "chat"):
        if lane in word:
            return f"free-{lane}"
    return None


def pick_brain(messages):
    """Choose the job for the newest user message: vision / long / coder / smart / chat."""
    last = next((m for m in reversed(messages) if m.get("role") == "user"), {})
    content = last.get("content", "")
    if isinstance(content, list):
        if any(part.get("type") == "image_url" for part in content if isinstance(part, dict)):
            return "free-vision"
        content = " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    total = sum(len(m["content"]) if isinstance(m.get("content"), str) else 0 for m in messages)
    text = content.lower()
    if total > 60000 or len(content) > 25000:
        return "free-long"
    if content.lstrip().startswith("### Task:"):  # Open WebUI's own background jobs (titles, tags): no need to sort
        return "free-chat"
    lane = ask_picker(messages, content)
    if lane:
        return lane
    # Picker unreachable (offline, Groq down or slow): fall back to the word lists
    if any(w in text for w in CODE_WORDS):
        return "free-coder"
    if any(w in text for w in SMART_WORDS):
        return "free-smart"
    return "free-chat"


def images(prompt, n=1, size="512x512"):
    w, h = (int(x) for x in re.findall(r"\d+", size or "512x512")[:2]) if re.search(r"\d+x\d+", size or "") else (512, 512)
    w, h = min(w, 768), min(h, 768)  # CPU: keep it reasonable
    with _img_lock, tempfile.TemporaryDirectory() as out:  # one picture job at a time
        r = subprocess.run([IMAGINE, prompt, "-n", str(max(1, min(n, 4))), "-W", str(w), "-H", str(h), "-o", out],
                           capture_output=True, text=True, timeout=900)
        files = sorted(f for f in os.listdir(out) if f.endswith(".png"))
        if not files:
            raise RuntimeError((r.stderr or r.stdout or "imagine made no picture")[-300:])
        return [{"b64_json": base64.b64encode(open(os.path.join(out, f), "rb").read()).decode()} for f in files]


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/v1/models"):
            self._send(200, json.dumps({"object": "list", "data": [{"id": "kokoro", "object": "model"},
                                                                   {"id": "fastsd-cpu", "object": "model"},
                                                                   {"id": "auto", "object": "model"}]}).encode())
        elif self.path.startswith("/v1/audio/voices"):
            self._send(200, json.dumps({"voices": ["bm_george", "bm_lewis", "bf_emma", "af_heart", "am_michael"]}).encode())
        else:
            self._send(404, b"{}")

    def auto_chat(self, data):
        """Pass the request to the brain switch with the job picked for it; stream the answer straight back."""
        import urllib.request
        job = pick_brain(data.get("messages", []))
        data["model"] = job
        key = open(os.path.expanduser("~/.config/crew/brain-switch.key")).read().strip()
        req = urllib.request.Request(SWITCH, json.dumps(data).encode(),
                                     {"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        try:
            resp = urllib.request.urlopen(req, timeout=300)
        except urllib.error.HTTPError as e:
            self._send(e.code, e.read()); return
        self.send_response(200)
        self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
        self.send_header("X-Brain-Job", job)
        self.end_headers()
        while True:
            chunk = resp.read1(65536) if hasattr(resp, "read1") else resp.read(65536)
            if not chunk:
                break
            self.wfile.write(chunk); self.wfile.flush()

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        if self.path == "/v1/chat/completions":
            try:
                self.auto_chat(data)
            except Exception as e:
                self._send(500, json.dumps({"error": {"message": f"Auto brain failed: {e}"}}).encode())
            return
        try:
            if self.path == "/v1/audio/speech":
                self._send(200, speech(str(data.get("input", "")), str(data.get("voice") or "bm_george"),
                                       float(data.get("speed") or 1.0)), "audio/wav")
            elif self.path == "/v1/images/generations":
                out = images(str(data.get("prompt", "")), int(data.get("n") or 1), str(data.get("size") or "512x512"))
                self._send(200, json.dumps({"created": int(time.time()), "data": out}).encode())
            else:
                self._send(404, b"{}")
        except Exception as e:
            self._send(500, json.dumps({"error": {"message": str(e)}}).encode())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    threading.Thread(target=unloader, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", 8898), Handler).serve_forever()
