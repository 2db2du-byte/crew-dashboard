"""Free AI Lab: run Rabbid's free AI tools from Mission Control.

One job at a time (the laptop has 15 GB RAM and no graphics card), heavy jobs refuse to
start when memory is low, and results are served back to the page from the output folders.
"""
import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
MOUNTS = "/run/media/" + __import__("os").environ.get("USER", "user")  # where removable drives mount

HOME = Path.home()
BIN = HOME / ".local/bin"
SEAGATE = Path(MOUNTS + "/OmarchyExt1")
OUT = SEAGATE / "ai/output"
INBOX = SEAGATE / "ai/input"
RESEARCH = HOME / "SecondBrain/3 Resources/Research"
DAILY = HOME / "SecondBrain/Daily"
ALLOWED_ROOTS = [OUT, INBOX, RESEARCH, DAILY]
MIN_FREE_MB_HEAVY = 4000

MEDIA = {".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image",
         ".wav": "audio", ".mp3": "audio", ".m4a": "audio", ".m4b": "audio",
         ".mp4": "video", ".webm": "video", ".md": "note", ".txt": "text", ".srt": "text"}


def _lines(text, n):
    return [l.strip() for l in text.splitlines() if l.strip()][:n]


TOOLS = {
    "imagine": {"name": "Make a picture", "emoji": "🖼️", "input": "text", "heavy": True,
                "hint": "a cozy cabin in the snow, cartoon style", "time": "1-3 min",
                "out": OUT / "images", "cmd": lambda t, f, o: [BIN / "imagine", t, "-o", o]},
    "cutout": {"name": "Remove a background", "emoji": "✂️", "input": "file", "accept": "image/*", "heavy": False,
               "hint": "Drop a photo", "time": "~40 sec",
               "out": OUT / "cutouts", "cmd": lambda t, f, o: [BIN / "cutout", f, str(Path(o) / (Path(f).stem + "-cutout.png"))]},
    "say": {"name": "Say it (Kokoro voice)", "emoji": "🗣️", "input": "text", "heavy": False,
            "hint": "Hey Rabbid, dinner's ready!", "time": "~30 sec",
            "out": None, "cmd": lambda t, f, o: [BIN / "say-kokoro", t]},
    "music": {"name": "Make music", "emoji": "🎵", "input": "text", "heavy": True,
              "hint": "chill acoustic guitar, campfire vibe", "time": "3-6 min",
              "out": OUT / "music", "cmd": lambda t, f, o: ["env", "NO_PLAY=1", BIN / "make-music", t, "12"]},
    "short": {"name": "Make a short video", "emoji": "📱", "input": "text", "heavy": False,
              "hint": "TITLE on the first line\nthen up to 3 lines of text", "time": "~1 min",
              "out": OUT / "shorts", "cmd": lambda t, f, o: [BIN / "make-short", *_lines(t, 4)]},
    "clips": {"name": "Long video → shorts", "emoji": "🎞️", "input": "file", "accept": "video/*,audio/*", "heavy": True,
              "hint": "Drop a long video or podcast", "time": "10-40 min",
              "out": OUT / "shorts", "cmd": lambda t, f, o: [BIN / "clip-shorts", f, "3"]},
    "transcribe": {"name": "Speech → text", "emoji": "📝", "input": "file", "accept": "video/*,audio/*", "heavy": True,
                   "hint": "Drop a video or recording", "time": "a few min",
                   "out": None, "cmd": lambda t, f, o: [BIN / "transcribe", f]},
    "audiobook": {"name": "Ebook → audiobook", "emoji": "🎧", "input": "file", "accept": ".epub", "heavy": True,
                  "hint": "Drop an EPUB ebook", "time": "hours for a whole book",
                  "out": OUT / "audiobooks", "cmd": lambda t, f, o: [BIN / "audiblez", f, "-v", "af_heart", "-o", o]},
    "describe": {"name": "Describe a picture", "emoji": "👁️", "input": "file", "accept": "image/*", "heavy": False,
                 "hint": "Drop a photo; the AI says what's in it and reads any writing", "time": "~1-2 min",
                 "out": OUT / "descriptions", "cmd": lambda t, f, o: [BIN / "describe-picture", f]},
    "translate": {"name": "Translate", "emoji": "🌍", "input": "text", "heavy": False,
                  "hint": "to spanish: Dinner is at six\n(languages: spanish, english, french, german, italian, portuguese, chinese, japanese)", "time": "~5 sec",
                  "out": OUT / "translations", "cmd": lambda t, f, o: [BIN / "translate", t]},
    "karaoke": {"name": "Karaoke (split a song)", "emoji": "🎤", "input": "file", "accept": "audio/*", "heavy": True,
                "hint": "Drop a song: get the singing and the music as two files", "time": "~2-5 min",
                "out": OUT / "stems", "cmd": lambda t, f, o: [BIN / "karaoke", f]},
    "research": {"name": "Overnight research (free, slow)", "emoji": "🌙", "input": "text", "heavy": True,
                 "hint": "Big question to dig into while you sleep. For quick answers, use Ask Claude.", "time": "~25 min",
                 "out": RESEARCH, "cmd": lambda t, f, o: [BIN / "research", t]},
    "meeseeks": {"name": "Mr. Meeseeks: one job", "emoji": "🔵", "input": "text", "heavy": False,
                 "hint": "Write a grocery list for tacos", "time": "~20 sec",
                 "out": DAILY, "cmd": lambda t, f, o: [BIN / "meeseeks", t]},
}

_jobs = []           # newest last
_queue = []
_lock = threading.Lock()
_wake = threading.Event()


def tools_public():
    return [{"key": k, **{f: v[f] for f in ("name", "emoji", "input", "hint", "time", "heavy")}, "accept": v.get("accept", "")}
            for k, v in TOOLS.items()]


def free_mb():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) // 1024
    return 0


def submit(tool, text="", file=None):
    if tool not in TOOLS:
        return {"ok": False, "error": "Unknown tool"}
    t = TOOLS[tool]
    if t["input"] == "text" and not text.strip():
        return {"ok": False, "error": "Type something first"}
    if t["input"] == "file" and not file:
        return {"ok": False, "error": "Drop a file first"}
    if not SEAGATE.is_mount():
        return {"ok": False, "error": "The Seagate isn't plugged in"}
    job = {"id": uuid.uuid4().hex[:8], "tool": tool, "name": t["name"], "emoji": t["emoji"],
           "text": text.strip()[:300], "file": Path(file).name if file else "", "_file": file,
           "state": "queued", "created": time.time(), "started": None, "ended": None,
           "results": [], "message": ""}
    with _lock:
        _jobs.append(job)
        _queue.append(job)
        del _jobs[:-40]
    _wake.set()
    return {"ok": True, "id": job["id"]}


def upload_path(name):
    day = INBOX / time.strftime("%Y-%m-%d")
    day.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip() or "upload"
    path = day / safe
    if path.exists():
        path = day / f"{path.stem}-{uuid.uuid4().hex[:4]}{path.suffix}"
    return path


def _new_files(roots, since):
    found = []
    for root in roots:
        if root and Path(root).exists():
            for p in Path(root).rglob("*"):
                if p.is_file() and p.stat().st_mtime >= since - 1 and p.suffix.lower() in MEDIA:
                    found.append(p)
    found.sort(key=lambda p: p.stat().st_mtime)
    return [{"path": str(p), "name": p.name, "kind": MEDIA[p.suffix.lower()]} for p in found[-12:]]


def _run(job):
    t = TOOLS[job["tool"]]
    if t["heavy"]:
        while free_mb() < MIN_FREE_MB_HEAVY:
            job["state"], job["message"] = "waiting", f"Waiting for free memory ({free_mb()} MB free, need {MIN_FREE_MB_HEAVY})"
            time.sleep(20)
    out = t["out"]
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
    job.update(state="running", started=time.time(), message="")
    argv = [str(a) for a in t["cmd"](job["text"], job["_file"], str(out) if out else "")]
    log = OUT / "lab-logs" / f"{job['id']}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PATH=f"{BIN}:{HOME}/.local/share/mise/shims:/usr/local/bin:/usr/bin:/bin")
    try:
        with log.open("w") as fh:
            rc = subprocess.run(argv, stdout=fh, stderr=subprocess.STDOUT, env=env, timeout=6 * 3600,
                                cwd=str(OUT)).returncode
    except subprocess.TimeoutExpired:
        rc = -1
    roots = [out] + ([Path(job["_file"]).parent] if job["_file"] else [])
    job["results"] = _new_files(roots, job["started"])
    if job["_file"]:
        job["results"] = [r for r in job["results"] if r["path"] != job["_file"]]
    tail = log.read_text(errors="replace").strip().splitlines()[-3:]
    job.update(state="done" if rc == 0 else "failed", ended=time.time(),
               message=" ".join(tail)[-300:] if rc != 0 or not job["results"] else "")


def _worker():
    while True:
        _wake.wait(5)
        _wake.clear()
        while True:
            with _lock:
                job = _queue.pop(0) if _queue else None
            if not job:
                break
            try:
                _run(job)
            except Exception as e:  # never let one bad job stop the lab
                job.update(state="failed", ended=time.time(), message=str(e)[:300])


def jobs_public():
    with _lock:
        return [{k: v for k, v in j.items() if not k.startswith("_")} for j in reversed(_jobs)]


def file_allowed(path):
    try:
        p = Path(path).resolve()
    except OSError:
        return None
    return p if p.is_file() and any(str(p).startswith(str(r.resolve())) for r in ALLOWED_ROOTS if r.exists()) else None


def open_folder(path):
    p = file_allowed(path)
    if p:
        subprocess.Popen(["xdg-open", str(p.parent)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        return True
    return False


threading.Thread(target=_worker, daemon=True).start()
