#!/usr/bin/env python3
"""Crew dashboard: live status of Rick's agent crew. Serves on 127.0.0.1:8899 only."""
import json, os, re, shutil, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
MOUNTS = "/run/media/" + __import__("os").environ.get("USER", "user")  # where removable drives mount

HOME = Path.home()
HERE = Path(__file__).parent
LOG = HOME / ".local/share/crew/activity.jsonl"
COURSE = HOME / "SecondBrain/1 Projects/Learn Linux.md"
INBOX = HOME / "SecondBrain/0 Inbox/Inbox.md"
PROJECTS = HOME / "SecondBrain/1 Projects"
BACKUP_DRIVE = MOUNTS + "/OmarchyExt2"  # weekly backup drive (lives in a drawer)
SEAGATE = MOUNTS + "/OmarchyExt1"        # nightly backups land here (KopiaBackup)

CREW = [
    ("rick", "Rick", "🧪", "Head master"),
    ("morty", "Morty", "😰", "Linux tutor"),
    ("summer", "Summer", "📓", "Second brain"),
    ("birdperson", "Birdperson", "🐦", "Backups & drives"),
    ("beth", "Beth", "🩺", "Home lab"),
    ("gearhead", "Gearhead", "🔧", "Devices"),
    ("unity", "Unity", "🌐", "Web & private search"),
    ("noob-noob", "Noob-Noob", "🧹", "Seagate caretaker"),
    ("mr-meeseeks", "Mr. Meeseeks", "🔵", "One-off jobs"),
    ("snoopy", "Snoopy", "🐶", "Free AIs keeper"),
    ("woodstock", "Woodstock", "🐤", "Firefox browser"),
    ("poopybutthole", "Mr. Poopybutthole", "⭐", "Hype man · online presence"),
    ("linus", "Linus", "🛡️", "Cybersecurity teacher · lab"),
]


def run(cmd, timeout=3):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""


def systemd_show(unit, *props):
    out = run(["systemctl", "--user", "show", unit, "-p", ",".join(props)])
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def activity():
    if not LOG.exists():
        return []
    lines = LOG.read_text().splitlines()[-200:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def backup():
    running = run(["systemctl", "--user", "is-active", "kopia-backup.service"]) in ("active", "activating") \
        or bool(run(["pgrep", "-f", "^/app/KopiaUI/resources/server/kopia snapshot create"]))
    lines, pct = [], None
    svc = systemd_show("kopia-backup.service", "Result", "ExecMainExitTimestamp")
    if running:
        lines.append("Backing up now…")
    elif svc.get("ExecMainExitTimestamp"):
        ok = svc.get("Result") == "success"
        lines.append(f"{'✅' if ok else '❌'} Last backup: {svc['ExecMainExitTimestamp'][:20]}{'' if ok else ' (problem!)'}")
    if os.path.ismount(SEAGATE):
        u = shutil.disk_usage(SEAGATE)
        lines.append(f"Nightly → Seagate: {u.free/1e9:.0f} GB free")
    else:
        lines.append("❌ Seagate not plugged in: nightly backup can't run")
    try:
        t = int((HOME / ".local/share/crew/last-1tb-backup").read_text())
        lines.append(f"Weekly → 1TB drive: last {time.strftime('%a %b %-d', time.localtime(t))}")
    except Exception:
        lines.append("Weekly → 1TB drive: not done yet")
    if os.path.ismount(BACKUP_DRIVE):
        lines.append("1TB drive is plugged in")
    nxt = systemd_show("kopia-backup.timer", "NextElapseUSecRealtime").get("NextElapseUSecRealtime")
    if nxt:
        lines.append(f"Next: {nxt[:20]}")
    # Weekly reminder (~/.local/bin/backup-reminder): due on Sundays until the drive is plugged in or Rabbid dismisses it.
    try:
        due = (HOME / ".local/share/crew/backup-reminder").read_text().split()[0] == "due"
    except Exception:
        due = False
    if due:
        lines.insert(0, "⚠️ BACKUP DAY: plug in the 1TB drive (reminding you every hour)")
    lines.append("📅 Every Sunday: plug in the 1TB drive for the weekly backup")
    doing = "Backing up your files" if running else ("Waiting for the 1TB drive: backup day!" if due else "")
    return {"busy": running or due, "doing": doing, "lines": lines, "progress": pct, "due": due}


def homelab():
    # Only the home lab's own containers (not the crew's n8n or the free apps)
    names = [n for n in run(["docker", "ps", "--format", "{{.Names}}"]).split() if not n.startswith(("app-", "crew-"))]
    apps = sorted({n.split("-")[0].split("_")[0] for n in names if n})
    return {"busy": bool(apps), "doing": "Running the home lab" if apps else "",
            "lines": [("Running: " + ", ".join(apps)) if apps else "All home lab apps stopped"]}


CYBER = HOME / "SecondBrain/1 Projects/Learn Cybersecurity.md"
BADGES = HOME / "SecondBrain/3 Resources/My certificates and badges.md"


def badges():
    """(earned, studying) from Rabbid's trophy case note."""
    if not BADGES.exists():
        return [], []
    sec, earned, studying = None, [], []
    for line in BADGES.read_text().splitlines():
        if line.startswith("## "):
            sec = line[3:].strip().lower()
        elif sec == "earned" and line.startswith("|") and not re.match(r"^\|\s*(Date|-)", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[1]:
                earned.append(cells[1])
        elif sec == "currently studying" and line.startswith("- "):
            studying.append(line[2:].strip())
    return earned, studying


def cyber():
    d = course(CYBER)
    earned, studying = badges()
    d["lines"].append(f"🏅 {len(earned)} badge(s) earned" + (f" · studying: {studying[0]}" if studying else ""))
    return d


def course(path=COURSE):
    if not path.exists():
        return {"lines": ["No course found"]}
    unit = task = None
    done = total = 0
    heading = ""
    for line in path.read_text().splitlines():
        if line.startswith("## Unit") or line.startswith("## 🏅"):
            heading = line[3:]
        elif line.startswith("- [x]"):
            done += 1; total += 1
        elif line.startswith("- [ ]"):
            total += 1
            if task is None:
                unit, task = heading, re.sub(r"[*`]", "", line[6:])
    lines = [f"{done} of {total} steps done"]
    if task:
        lines += [re.sub(r"\s*\(week.*?\)", "", unit), f"Next: {task}"]
    return {"lines": lines, "progress": round(done / total * 100) if total else 0}


def brain():
    inbox = [l for l in INBOX.read_text().splitlines() if l.startswith("- ")] if INBOX.exists() else []
    projects = len(list(PROJECTS.glob("*.md")))
    return {"lines": [f"{len(inbox)} item(s) in the Inbox", f"{projects} open projects"]}


SEAGATE = MOUNTS + "/OmarchyExt1"


def seagate():
    if not os.path.ismount(SEAGATE):
        return {"lines": ["Seagate not plugged in"]}
    u = shutil.disk_usage(SEAGATE)
    lines = [f"{u.used/1e9:.0f} GB used, {u.free/1e12:.1f} TB free"]
    inst = Path(SEAGATE, "ai/INSTALLED.txt")
    n = len(inst.read_text().splitlines()) if inst.exists() else 0
    lines.append(f"{n} AI install(s) on the drive")
    return {"lines": lines, "progress": round(u.used / u.total * 100)}


def web():
    firefox = bool(run(["pgrep", "-f", "org.mozilla.firefox"]))
    return {"lines": ["🦊 Firefox: " + ("open" if firefox else "closed"),
                      "🔎 SearXNG private search: " + ("on" if port_up(8888) else "off"),
                      "✨ Firefox AI sidebar → Open WebUI: " + ("ready" if port_up(3080) and port_up(4000) else "brains offline")]}


LIBRARY_DIR = Path(MOUNTS + "/OmarchyExt1/Offline Library/Wikipedia and more (zim files)")


def free_ais():
    """Snoopy's doghouse: the free AIs (Ollama, Open WebUI, the offline library, news, voice + pictures)."""
    lines = []
    try:
        loaded = json.load(urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=2)).get("models", [])
        lines.append("🧠 Loaded: " + (", ".join(f"{m['name'].split(':latest')[0]} ({m['size']/1e9:.1f} GB)" for m in loaded) or "none (RAM free)"))
    except Exception:
        lines.append("❌ Ollama isn't answering")
    with open("/proc/meminfo") as fh:
        mem = {l.split(":")[0]: int(l.split()[1]) for l in fh}
    lines.append(f"💾 RAM free: {mem['MemAvailable']/1e6:.1f} of {mem['MemTotal']/1e6:.0f} GB")
    lines.append("💬 Open WebUI: " + ("on" if port_up(3080) else "off") + " · 🎙🎨 voice/pictures: " + ("on" if port_up(8898) else "off"))
    busy = False
    if LIBRARY_DIR.is_dir():
        names = os.listdir(LIBRARY_DIR)
        books, parts = sum(n.endswith(".zim") for n in names), [n for n in names if n.endswith(".part")]
        busy = bool(parts)
        lines.append(f"📚 Library: {books} books" + (f" · downloading {parts[0].split('_en_')[0]}" if parts else ""))
    else:
        lines.append("📚 Library: Seagate not plugged in")
    return {"busy": busy, "doing": "Fetching new books for the library" if busy else "", "lines": lines}


def brain_json(system, user, local_model, timeout=600, job="free-chat", agent=None):
    """A JSON answer from the free AI brains: cloud via the brain switch when online, the local model otherwise.
    With an agent, its Crew School lessons go into the prompt and the job is kept for the nightly coach."""
    if agent:
        role = next((r for k, _, _, r in CREW if k == agent), "")
        out = brain_json(system + memory.block(agent, user, role), user, local_model, timeout, job)
        try:
            lessons.record_run(agent, system, user, local_model, job, out)
        except OSError:
            pass
        return out
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        key = (HOME / ".config/crew/brain-switch.key").read_text().strip()
        req = urllib.request.Request("http://127.0.0.1:4000/v1/chat/completions",
                                     json.dumps({"model": job, "messages": msgs, "temperature": 0.5,
                                                 "response_format": {"type": "json_object"}}).encode(),
                                     {"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        out = json.load(urllib.request.urlopen(req, timeout=90))["choices"][0]["message"]["content"]
        json.loads(re.sub(r"^```(json)?|```$", "", out.strip()).strip())  # must be real JSON
        return re.sub(r"^```(json)?|```$", "", out.strip()).strip()
    except Exception:
        body = json.dumps({"model": local_model, "stream": False, "think": False, "format": "json",
                           "options": {"temperature": 0.5}, "messages": msgs}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/chat", body, {"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read())["message"]["content"]


_brains = {"t": 0, "data": []}


def brains_status():
    """Which free brains are reachable right now (cheap 'list models' checks, no AI uses). Cached 5 minutes."""
    if time.time() - _brains["t"] < 300 and _brains["data"]:
        return _brains["data"]
    keys = {}
    try:
        for line in (HOME / ".config/crew/ai-keys.env").read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1); keys[k.strip()] = v.strip()
    except Exception:
        pass

    def probe(url, headers):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers | {"User-Agent": "curl/8"}), timeout=8).status == 200
        except Exception:
            return False
    cf = keys.get("CLOUDFLARE_ACCOUNT_ID", "")
    checks = [
        ("Groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1/models", {"Authorization": f"Bearer {keys.get('GROQ_API_KEY', '')}"}),
        ("Gemini", "GEMINI_API_KEY", f"https://generativelanguage.googleapis.com/v1beta/models?key={keys.get('GEMINI_API_KEY', '')}", {}),
        ("Cloudflare", "CLOUDFLARE_API_TOKEN", f"https://api.cloudflare.com/client/v4/accounts/{cf}/ai/models/search?per_page=1",
         {"Authorization": f"Bearer {keys.get('CLOUDFLARE_API_TOKEN', '')}"}),
        ("OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/key", {"Authorization": f"Bearer {keys.get('OPENROUTER_API_KEY', '')}"}),
        ("Mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1/models", {"Authorization": f"Bearer {keys.get('MISTRAL_API_KEY', '')}"}),
        ("NVIDIA", "NVIDIA_NIM_API_KEY", "https://integrate.api.nvidia.com/v1/models", {"Authorization": f"Bearer {keys.get('NVIDIA_NIM_API_KEY', '')}"}),
        ("Ollama Cloud", "OLLAMA_API_KEY", "https://ollama.com/api/tags", {"Authorization": f"Bearer {keys.get('OLLAMA_API_KEY', '')}"}),
    ]
    out = [{"name": n, "up": bool(keys.get(k)) and probe(u, h), "note": "no key" if not keys.get(k) else ""} for n, k, u, h in checks]
    out.append({"name": "Brain switch", "up": port_up(4000), "note": "routes to the brains"})
    out.append({"name": "Local AI", "up": port_up(11434), "note": "used when offline"})
    _brains.update(t=time.time(), data=out)
    return out


def to_empty_workspace():
    """Things launched from Mission Control open on the next empty workspace (on the screen Mission Control is on),
    not squeezed in next to it."""
    run(["hyprctl", "dispatch", 'hl.dsp.focus({ workspace = "emptym" })'])


def firefox_status():
    up = bool(run(["pgrep", "-f", "org.mozilla.firefox"])) or bool(run(["pgrep", "-x", "firefox"]))
    return {"lines": ["🦊 Firefox: " + ("open" if up else "closed") + " · click me to open it",
                      "🎵 Apple Music is on the bookmarks bar"]}


GH_USER = "2db2du-byte"
HF_USER = "RabbidRaccoon"
HF_SPACES = ("rabbids-lab", "ask-rick")
HF_COLLECTION = "RabbidRaccoon/free-ais-on-a-laptop-with-no-gpu-6ac694416841d750eb0872df"
_gh = {"t": 0, "data": None}


def github_status():
    """Mr. Poopybutthole's booth: Rabbid's public GitHub + Hugging Face. Public APIs only (no login), cached 30 minutes."""
    if time.time() - _gh["t"] < 1800 and _gh["data"]:
        return _gh["data"]
    lines, problems = [], []
    def get(url, timeout=8):
        req = urllib.request.Request(url, headers={"User-Agent": "mission-control", "Accept": "application/vnd.github+json"})
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    try:
        user = get(f"https://api.github.com/users/{GH_USER}")
        repos = get(f"https://api.github.com/users/{GH_USER}/repos?per_page=100")
        stars = sum(r.get("stargazers_count", 0) for r in repos)
        forks = sum(r.get("forks_count", 0) for r in repos)
        lines.append(f"🐙 {user.get('public_repos', len(repos))} public repos · ⭐ {stars} stars · 🍴 {forks} forks · 👥 {user.get('followers', 0)} followers")
        bare = [r["name"] for r in repos if not r.get("description") or not r.get("topics")]
        if bare:
            problems.append("missing a description or tags: " + ", ".join(bare))
        try:
            snake = get(f"https://api.github.com/repos/{GH_USER}/{GH_USER}/commits?sha=output&per_page=1")[0]["commit"]["committer"]["date"]
            age = (time.time() - time.mktime(time.strptime(snake, "%Y-%m-%dT%H:%M:%SZ")) + time.timezone) / 3600
            lines.append(f"🐍 Snake redrawn {age:.0f} h ago")
            if age > 36:
                problems.append(f"the contribution snake hasn't redrawn in {age:.0f} hours")
        except Exception:
            problems.append("couldn't find the contribution snake")
    except Exception as e:
        lines.append(f"❌ GitHub didn't answer ({str(e)[:60]})")
    # Hugging Face: the profile, both Spaces (must be RUNNING) and the Collection.
    try:
        hf = get(f"https://huggingface.co/api/users/{HF_USER}/overview")
        spaces = get(f"https://huggingface.co/api/spaces?author={HF_USER}&full=true")
        likes = sum(sp.get("likes", 0) for sp in spaces)
        lines.append(f"🤗 Hugging Face: {len(spaces)} Spaces · ❤️ {likes} likes · 👥 {hf.get('numFollowers', 0)} followers")
        for name in HF_SPACES:
            st = get(f"https://huggingface.co/api/spaces/{HF_USER}/{name}").get("runtime", {}).get("stage", "?")
            if st != "RUNNING":
                problems.append(f"the {name} Space is {st}")
        coll = get(f"https://huggingface.co/api/collections/{HF_COLLECTION}")
        if len(coll.get("items", [])) < 15:
            problems.append("the Hugging Face collection lost items")
    except Exception as e:
        lines.append(f"🤗 Hugging Face didn't answer ({str(e)[:50]})")
    try:
        code = urllib.request.urlopen(f"https://{GH_USER}.github.io/", timeout=8).status
        lines.append("🌐 Homepage: " + ("up" if code == 200 else f"HTTP {code}"))
        if code != 200:
            problems.append("the homepage is down")
    except Exception:
        lines.append("🌐 Homepage: down")
        problems.append("the homepage is down")
    # Local projects changed since their cleaned public copies were last published?
    try:
        import importlib.machinery
        ex = importlib.machinery.SourceFileLoader("publish_export", str(HOME / "Projects/publish/export.py")).load_module()
        stale = []
        for repo, files in ex.REPOS.items():
            out = ex.OUT / repo / ".git"
            last = float(run(["git", "-C", str(ex.OUT / repo), "log", "-1", "--format=%ct"]) or 0) if out.exists() else 0
            for spec in files:
                src = spec.split(":")[0]
                src = Path(src) if src.startswith("/") else ex.P / src
                if src.exists() and src.stat().st_mtime > last + 60:
                    stale.append(repo)
                    break
        lines.append("📦 Public copies: " + ("all up to date" if not stale else "changed on the laptop since last upload: " + ", ".join(stale)))
        if stale:
            problems.append("new changes waiting to be uploaded (" + ", ".join(stale) + ")")
    except Exception as e:
        lines.append(f"📦 Couldn't check the public copies ({str(e)[:50]})")
    # Every site up and linking to every other site (GitHub, homepage, Spaces, Hugging Face, Ollama, Bluesky).
    pc = run([str(HOME / ".local/bin/presence-check")], timeout=120)
    if pc:
        bsky = [l for l in pc.splitlines() if "Bluesky profile" in l]
        if bsky:
            lines.append("🦋 " + bsky[0].lstrip("✅⚠️❌ ").replace("Bluesky profile", "Bluesky").strip())
        broken = [l.lstrip("⚠️❌ ") for l in pc.splitlines() if l.startswith(("⚠", "❌"))]
        lines.append("🔗 Cross-links: " + ("every site links to every other site" if not broken else f"{len(broken)} problem(s)"))
        problems += broken
    lines.append("✅ Looking bad-ass" if not problems else "⚠️ Needs love: " + "; ".join(problems))
    _gh.update(t=time.time(), data={"lines": lines})
    return _gh["data"]


def devices():
    lines = []
    adb = run(["adb", "devices"])
    phone = any(l.endswith("\tdevice") for l in adb.splitlines()[1:])
    lines.append("📱 Android phone: " + ("connected by USB" if phone else "not plugged in"))
    ts = run(["tailscale", "status", "--peers=false"], timeout=2)
    lines.append("🔒 Tailscale: " + ("on" if ts and "stopped" not in ts.lower() else "off"))
    return {"lines": lines}


APPS = [  # the launch pad: (name, emoji, port, what it is)
    ("n8n", "⚙️", 5678, "Crew's job runner"),
    ("Open WebUI", "💬", 3080, "Chat with the free AIs"),
    ("Open Notebook", "📒", 8502, "Your own NotebookLM"),
    ("Immich", "📸", 2283, "Your photos, Google Photos style (homelab start immich)"),
    ("Jellyfin", "🎬", 8096, "Family videos, Netflix style (homelab start jellyfin)"),
    ("Audiobookshelf", "🎧", 13378, "Family audiobooks"),
    ("File Browser", "🗂️", 8085, "Files from any device"),
    ("FreshRSS", "📰", 8086, "News, no algorithm"),
    ("Forgejo", "🧰", 3001, "Your code, safe at home"),
    ("Stirling PDF", "📄", 8087, "PDF toolkit"),
    ("SearXNG", "🔎", 8888, "Private search"),
    ("Kolibri", "🎓", 8081, "Offline school for the kids"),
    ("Translate", "🌍", 5100, "LibreTranslate: offline translation"),
    ("Offline Library", "📚", 8090, "Wikipedia, textbooks, repair, medicine, survival: offline (Kiwix)"),
    ("Offline Maps", "🗺️", 8091, "US maps with no internet (Project NOMAD's maps)"),
    ("Sunshine", "☀️", 47990, "Stream this laptop to phone/TV (Moonlight)"),
    ("MoneyPrinter", "💸", 8501, "Topic to short video (run: moneyprinter)"),
    ("ComfyUI", "🎨", 8188, "AI picture workshop (run: comfyui)"),
]


def port_up(port):
    import socket
    with socket.socket() as sk:
        sk.settimeout(0.3)
        return sk.connect_ex(("127.0.0.1", port)) == 0


def apps_status():
    return [{"name": n, "emoji": e, "url": f"{'https' if p == 47990 else 'http'}://127.0.0.1:{p}/", "what": w, "up": port_up(p)} for n, e, p, w in APPS]


_usage = {"t": 0, "data": None}


def claude_usage():
    """Rabbid's Claude Pro plan meter (5-hour session + week), from his Claude Code login. Cached 2 minutes.
    Only the two percentages and reset times leave this function; the login token never does."""
    if time.time() - _usage["t"] < 120 and _usage["data"]:
        return _usage["data"]
    try:
        tok = json.loads((HOME / ".claude/.credentials.json").read_text())["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
            "Authorization": f"Bearer {tok}", "anthropic-beta": "oauth-2025-04-20", "Content-Type": "application/json"})
        raw = json.load(urllib.request.urlopen(req, timeout=15))
        data = {k: {"utilization": raw[k]["utilization"], "resets_at": raw[k]["resets_at"]} if raw.get(k) else None
                for k in ("five_hour", "seven_day")}
    except urllib.error.HTTPError as e:
        data = {"error": "open Claude to refresh the login" if e.code == 401 else f"usage check failed ({e.code})"}
    except Exception:
        data = {"error": "can't reach Claude (offline?)"}
    _usage.update(t=time.time(), data=data)
    return data


def rick_running():
    """True if a `claude --agent rick` session is open (checks real argv, not shell text)."""
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            argv = (proc / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if argv and argv[0].endswith(b"claude") and b"--agent" in argv:
            i = argv.index(b"--agent")
            if i + 1 < len(argv) and argv[i + 1] == b"rick":
                return True
    return False


_cache = {"t": 0, "data": None}


def status():
    if time.time() - _cache["t"] < 4 and _cache["data"]:
        return _cache["data"]
    acts = activity()
    now = time.time()
    last = {}
    for a in acts:
        last[a["agent"]] = a
    rick_live = rick_running()
    domain = {"birdperson": backup(), "beth": homelab(), "morty": course(),
              "summer": brain(), "gearhead": devices(), "noob-noob": seagate(), "unity": web(),
              "snoopy": free_ais(), "woodstock": firefox_status(), "poopybutthole": github_status(), "linus": cyber()}
    crew = []
    for key, name, emoji, role in CREW:
        d = domain.get(key, {})
        a = last.get(key)
        working = bool(a and a["event"] in ("PreToolUse", "start") and now - a["t"] < 7200)
        state = "working" if working else ("busy" if d.get("busy") else "idle")
        doing = a["task"] if working else d.get("doing", "")
        if key == "rick":
            state = "working" if (rick_live or any(
                x["event"] in ("PreToolUse", "start") and now - x["t"] < 7200 and last.get(x["agent"]) is x for x in acts)) else "idle"
            doing = "Running the crew" if state == "working" else ""
        jobs = sum(1 for x in acts if x["agent"] == key and x["event"] in ("PostToolUse", "done"))
        lines = list(d.get("lines", []))
        if key in ("mr-meeseeks", "rick") or not lines:
            lines.append(f"{jobs} job(s) done" if key != "rick" else
                         f"{sum(1 for x in acts if x['event'] in ('PostToolUse', 'done'))} crew job(s) done")
        if a and not working and key != "rick":
            lines.append(f"Last job: {a['task']}")
        crew.append({"key": key, "name": name, "emoji": emoji, "role": role, "state": state,
                     "doing": doing, "lines": lines, "progress": d.get("progress")})
    feed = [{"t": a["t"], "agent": a["agent"], "task": a["task"],
             "done": a["event"] in ("PostToolUse", "done")} for a in reversed(acts[-25:])]
    _cache.update(t=time.time(), data={"crew": crew, "feed": feed, "now": now})
    return _cache["data"]


# ---------------------------------------------------------------------------
# Crew API: what the n8n crew uses. Facts in, reports out. Localhost only.
# ---------------------------------------------------------------------------
DAILY = HOME / "SecondBrain/Daily"
NAMES = {k: (n, e) for k, n, e, _ in CREW}


def log_event(agent, task, event):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({"t": int(time.time()), "event": event, "agent": agent,
                            "task": task, "session": "n8n"}) + "\n")


def kopia_snapshots():
    # The nightly backups on the Seagate (the 1TB one is in a drawer most of the time).
    cfg = str(HOME / ".var/app/io.kopia.KopiaUI/config/kopia/seagate.config")
    out = run([str(HOME / ".local/bin/kopia"), "--config-file", cfg, "snapshot", "list", "--all", "--json"], timeout=90)
    try:
        snaps = json.loads(out)
    except ValueError:
        return ["Could not read the backup list (is the Seagate plugged in?)"]
    latest = {}
    for sn in snaps:
        path = sn["source"]["path"].replace(str(HOME), "~")
        latest[path] = max(latest.get(path, ""), sn["startTime"])
    return [f"{p}: last saved {t[:16].replace('T', ' ')} UTC" for p, t in sorted(latest.items())] or ["No backups saved yet"]


def facts(agent):
    """Plain-text facts about an agent's area, for its AI to report on."""
    now = time.strftime("%A %B %-d, %Y, %-I:%M %p")
    f = [f"Right now it is {now}."]
    if agent == "birdperson":
        b = backup()
        f += b["lines"]
        f.append("A backup is running right now." if b["busy"] else "No backup is running right now.")
        f += ["Saved backups per folder:"] + kopia_snapshots()
        f.append("The nightly backup to the Seagate is supposed to run every day at 8 PM. More than 2 days without a saved backup is a problem. "
                 "The 1TB drive lives in a drawer and gets a full backup on Sundays when Rabbid plugs it in; more than 8 days without one is a problem.")
    elif agent == "beth":
        f += homelab()["lines"]
        f.append("Home lab apps are started by hand with the homelab command; being stopped is normal.")
        f.append(f"Laptop disk: {shutil.disk_usage('/').free/1e9:.0f} GB free.")
    elif agent == "morty":
        f += course()["lines"]
    elif agent == "summer":
        inbox = [l[2:] for l in INBOX.read_text().splitlines() if l.startswith("- ")] if INBOX.exists() else []
        f.append(f"Inbox has {len(inbox)} item(s):")
        f += [f"- {x}" for x in inbox] or ["(empty)"]
        f.append("Open projects:")
        f += [f"- {p.stem}" for p in sorted(PROJECTS.glob("*.md"))]
    elif agent == "gearhead":
        f += devices()["lines"]
        bat = run(["cat", "/sys/class/power_supply/BAT1/capacity"]) or run(["sh", "-c", "cat /sys/class/power_supply/BAT*/capacity"])
        if bat:
            f.append(f"Laptop battery: {bat}%")
    elif agent == "noob-noob":
        f += seagate()["lines"]
        if os.path.ismount(SEAGATE):
            f.append("Folders on the Seagate: " + ", ".join(sorted(p.name for p in Path(SEAGATE).iterdir() if p.name != "lost+found")))
    elif agent == "snoopy":
        f += free_ais()["lines"]
    elif agent == "poopybutthole":
        _gh["t"] = 0
        f += github_status()["lines"]
        f.append("Rabbid's GitHub is github.com/2db2du-byte, his homepage is 2db2du-byte.github.io, and his Hugging Face is RabbidRaccoon "
                 "(Spaces: Rabbid's Lab and Ask Rick, plus a collection of the free AIs he runs). The public projects are cleaned "
                 "copies of what runs on his laptop; when they're out of date, Claude refreshes them on request (it scans out personal info first).")
        f.append("Open WebUI has 15 free models with Rabbid's Knowledge tool (library, notes, news, time, calculator), "
                 "Kokoro voice and FastSD pictures. Joshua is the voice butler. The library updates itself monthly.")
    elif agent == "linus":
        f += cyber()["lines"]
        earned, studying = badges()
        f.append("Badges earned: " + (", ".join(earned) or "none yet"))
        f.append("Currently studying: " + (", ".join(studying) or "nothing"))
        f.append("Rabbid isn't job hunting: the free certificates and badges are proof he learned it. Everything is free.")
    elif agent == "rick":
        for c in status()["crew"]:
            f.append(f"{c['name']} ({c['role']}): " + "; ".join(c["lines"]))
    elif agent == "unity":
        inbox = [l[2:] for l in INBOX.read_text().splitlines() if l.startswith("- ")] if INBOX.exists() else []
        f.append("Rabbid's ideas waiting in his Inbox:")
        f += [f"- {x}" for x in inbox] or ["(none)"]
        f.append("Rabbid's open projects: " + ", ".join(p.stem for p in sorted(PROJECTS.glob("*.md"))))
        f.append("His laptop has no graphics card; he likes free, local, private tools.")
    return "\n".join(f)


def strip_think(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def deliver(agent, data):
    """Take an agent's AI answer, file the report in today's Daily note, and alert Rabbid if needed."""
    raw = strip_think(data.get("answer", ""))
    try:
        ans = json.loads(raw)
    except ValueError:
        m = re.search(r"\{.*\}", raw, re.S)
        try:
            ans = json.loads(m.group(0)) if m else {"report": raw}
        except ValueError:
            ans = {"report": raw}
    rep = ans.get("report") or raw
    if isinstance(rep, list):
        rep = "\n".join(f"- {str(x).lstrip('- ').strip()}" for x in rep)
    elif isinstance(rep, dict):
        rep = "\n".join(f"- **{k}:** {v}" for k, v in rep.items())
    report = str(rep).strip()
    alert = bool(ans.get("alert")) or bool(data.get("always_alert"))
    speak = str(ans.get("say") or "").strip()
    name, emoji = NAMES.get(agent, (agent, "🤖"))
    day = time.strftime("%Y-%m-%d")
    note = DAILY / f"{day}.md"
    DAILY.mkdir(parents=True, exist_ok=True)
    if not note.exists():
        note.write_text(f"# {time.strftime('%A, %B %-d, %Y')}\n\n## 🧪 Crew reports\n")
    elif "## 🧪 Crew reports" not in note.read_text():
        with note.open("a") as fh:
            fh.write("\n## 🧪 Crew reports\n")
    with note.open("a") as fh:
        fh.write(f"\n### {emoji} {name} · {time.strftime('%-I:%M %p')}{' · ⚠️' if alert and not data.get('always_alert') else ''}\n{report}\n")
    if alert:
        subprocess.Popen(["notify-send", "-a", "Rick's crew", f"{emoji} {name}", (speak or report)[:300]])
    if speak and (alert or data.get("speak")):
        subprocess.Popen([str(HOME / ".local/bin/say"), speak[:600]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log_event(agent, data.get("task") or f"{name} report", "done")
    _cache["t"] = 0
    return {"ok": True, "alert": alert, "note": str(note)}


import lessons  # noqa: E402  (Crew School: lessons each member learns over time)
import memory  # noqa: E402  (what a member remembers before each job)
import lab  # noqa: E402  (Free AI Lab: runs the tools one at a time)
import kb  # noqa: E402  (knowledge for the free AIs: offline library, notes, time, math)
from urllib.parse import unquote, parse_qs, urlparse  # noqa: E402
import mimetypes  # noqa: E402


RICK_SYSTEM = (
    "You are Rick Sanchez from Rick and Morty, head master of Rabbid's agent crew: sarcastic genius, occasional *burp*, "
    "grudgingly fond of Rabbid. Keep it PG: no swearing, no drinking jokes. Use ONLY the facts you are given; never invent "
    "numbers or problems. Rabbid just asked you for a status update. "
    'Reply ONLY with JSON: {"report": "one short bullet per crew member worth mentioning, for his notes", '
    '"say": "a spoken update in character, 3 to 5 sentences, most important thing first", "alert": false}'
)
_rick_busy = threading.Lock()


def rick_update():
    """On-demand spoken status update from Rick (free local AI)."""
    if not _rick_busy.acquire(blocking=False):
        return
    try:
        log_event("rick", "Status update for Rabbid", "start")
        _cache["t"] = 0
        try:
            answer = brain_json(RICK_SYSTEM, facts("rick"), "qwen3:8b", job="free-smart", agent="rick")
        except Exception:
            answer = json.dumps({"report": "Couldn't reach the AI brain (Ollama).",
                                 "say": "Rabbid, my brain's offline. Ollama isn't answering. Tell Claude.", "alert": True})
        deliver("rick", {"answer": answer, "task": "Status update for Rabbid", "speak": True, "always_alert": True})
    finally:
        _rick_busy.release()


# Personas + models for on-demand updates come from the crew's own definitions (single source of truth).
import importlib.util as _ilu  # noqa: E402
_spec = _ilu.spec_from_file_location("crewdefs", str(HOME / "Projects/crew/make_workflows.py"))
_crewdefs = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_crewdefs)
CREWDEFS = {c["key"]: c for c in _crewdefs.CREW + getattr(_crewdefs, "ON_DEMAND", [])}
_busy = {}


def crew_update(agent):
    """On-demand spoken update from any crew member, on their own free model."""
    if agent == "rick":
        return rick_update()
    c = CREWDEFS.get(agent)
    lock = _busy.setdefault(agent, threading.Lock())
    if not c or not lock.acquire(blocking=False):
        return
    try:
        title = f"{c['title'].split('·')[0].strip()} · update for Rabbid"
        log_event(agent, title, "start")
        _cache["t"] = 0
        system = c["persona"] + " " + _crewdefs.COMMON + c["task"] + " Rabbid just clicked you and asked for this right now."
        try:
            answer = brain_json(system, facts(agent), c["model"], timeout=900, agent=agent)
        except Exception:
            answer = json.dumps({"report": "Couldn't reach the AI brain (Ollama).", "say": "Ollama isn't answering. Tell Claude.", "alert": True})
        deliver(agent, {"answer": answer, "task": title, "speak": True, "always_alert": True})
    finally:
        lock.release()


def who_is(system):
    """Which crew member an n8n job is for, from the persona at the start of its prompt."""
    if system.startswith("You are Mr. Meeseeks"):
        return "mr-meeseeks"
    for key, c in CREWDEFS.items():
        if system.startswith(c["persona"][:60]):
            return key
    return None


def school(agent):
    les = lessons.read(agent)
    mem = memory.MEM / f"{lessons.path(agent).stem}.md"
    diary = [l[2:] for l in mem.read_text().splitlines() if l.startswith("- ")][-12:] if mem.exists() else []
    return {"agent": agent, "lessons": les, "count": sum(len(v) for v in les.values()), "diary": diary,
            "jobs": len(lessons.runs(agent)), "version": lessons.version(agent)}


def crew_action(action, text=""):
    """Small one-click jobs from the crew cards. Only these exact actions are allowed."""
    def opn(target):
        subprocess.Popen(["xdg-open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    if action == "open-url":
        # Mission Control runs in a toolbar-free Firefox window (no tab bar), so its links open in Rabbid's main Firefox.
        url = text.strip()
        if not re.match(r"^https?://[^\s]+$", url):
            return {"ok": False, "note": "Not a web link."}
        opn(url)
        return {"ok": True, "note": "🦊 Opening in Firefox…"}
    if action == "open-course":
        opn("obsidian://open?vault=SecondBrain&file=1%20Projects%2FLearn%20Linux")
    elif action == "open-cyber":
        opn("obsidian://open?vault=SecondBrain&file=1%20Projects%2FLearn%20Cybersecurity")
    elif action == "credly-sync":
        r = subprocess.run([str(HOME / ".local/bin/credly-sync")], capture_output=True, text=True, timeout=40)
        return {"ok": r.returncode == 0, "note": (r.stdout or r.stderr).strip() or "Couldn't reach Credly."}
    elif action == "open-badges":
        opn("obsidian://open?vault=SecondBrain&file=3%20Resources%2FMy%20certificates%20and%20badges")
    elif action == "open-inbox":
        opn("obsidian://open?vault=SecondBrain&file=0%20Inbox%2FInbox")
    elif action == "backup-now":
        if run(["systemctl", "--user", "is-active", "kopia-backup.service"]) in ("active", "activating"):
            return {"ok": True, "note": "A backup is already running."}
        subprocess.Popen(["systemctl", "--user", "start", "--no-block", "kopia-backup.service"])
    elif action == "open-firefox":
        subprocess.Popen([str(HOME / ".local/bin/firefox-open")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        _cache["t"] = 0
        return {"ok": True, "note": "🦊 Opening Firefox…"}
    elif action == "open-webui":
        to_empty_workspace()
        subprocess.Popen(["omarchy-launch-or-focus-webapp", "Rick's Lab", "http://127.0.0.1:3080/"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    elif action == "free-ram":
        try:
            loaded = json.load(urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=3)).get("models", [])
        except Exception:
            return {"ok": False, "note": "Ollama isn't answering."}
        for m in loaded:
            run(["ollama", "stop", m["name"]], timeout=20)
        _cache["t"] = 0
        return {"ok": True, "note": f"🧹 Unloaded {len(loaded)} model(s)." if loaded else "Nothing loaded; RAM's already free."}
    elif action == "backup-dismiss":
        subprocess.run([str(HOME / ".local/bin/backup-reminder"), "dismiss"])
        _cache["t"] = 0
        return {"ok": True, "note": "🔕 Reminder off until next Sunday."}
    elif action == "open-brave":
        subprocess.Popen(["omarchy-launch-browser"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    elif action == "brave-search":
        from urllib.parse import quote_plus
        if not text.strip():
            return {"ok": False, "note": "Type what to search for."}
        opn(f"http://127.0.0.1:8888/search?q={quote_plus(text.strip()[:400])}")
    elif action == "meeseeks":
        if not text.strip():
            return {"ok": False, "note": "Type his one job first."}
        def job():
            req = urllib.request.Request("http://127.0.0.1:5678/webhook/meeseeks", json.dumps({"task": text.strip()[:1000]}).encode(),
                                         {"Content-Type": "application/json"})
            try:
                urllib.request.urlopen(req, timeout=900).read()
            except Exception:
                pass
        threading.Thread(target=job, daemon=True).start()
    else:
        return {"ok": False, "note": "Unknown action"}
    return {"ok": True}


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path):
        size = path.stat().st_size
        start, end = 0, size - 1
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            start = int(a) if a else 0
            end = int(b) if b else size - 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(path))[0] or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        with path.open("rb") as fh:
            fh.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = fh.read(min(1 << 20, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def do_GET(self):
        if self.path.startswith("/api/status"):
            body, ctype = json.dumps(status()).encode(), "application/json"
        elif self.path.startswith("/api/facts/"):
            agent = self.path.split("/")[3].split("?")[0]
            task = re.search(r"task=([^&]+)", self.path)
            from urllib.parse import unquote_plus
            log_event(agent, unquote_plus(task.group(1)) if task else f"{agent} check-in", "start")
            _cache["t"] = 0
            body, ctype = json.dumps({"agent": agent, "facts": facts(agent)}).encode(), "application/json"
        elif self.path.split("?")[0] in ("/", "/index.html"):
            body, ctype = (HERE / "index.html").read_bytes(), "text/html; charset=utf-8"
        elif self.path in ("/avatars.js", "/pixel.js"):
            body, ctype = (HERE / self.path[1:]).read_bytes(), "text/javascript; charset=utf-8"
        elif self.path == "/api/lab/tools":
            body, ctype = json.dumps({"tools": lab.tools_public(), "free_mb": lab.free_mb()}).encode(), "application/json"
        elif self.path == "/api/lab/jobs":
            body, ctype = json.dumps({"jobs": lab.jobs_public(), "free_mb": lab.free_mb()}).encode(), "application/json"
        elif self.path.startswith("/api/out?"):
            f = parse_qs(urlparse(self.path).query).get("f", [""])[0]
            p = lab.file_allowed(f)
            if not p:
                self.send_error(404); return
            try:
                self._send_file(p)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        elif self.path == "/api/brains":
            body, ctype = json.dumps(brains_status()).encode(), "application/json"
        elif self.path == "/api/claude-usage":
            body, ctype = json.dumps(claude_usage()).encode(), "application/json"
        elif self.path.split("?")[0] == "/school":
            body, ctype = (HERE / "school.html").read_bytes(), "text/html; charset=utf-8"
        elif self.path == "/api/school-scores":
            f = lessons.DATA / "school/scores.jsonl"
            rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []
            body, ctype = json.dumps(rows).encode(), "application/json"
        elif self.path.startswith("/api/school/"):
            agent = self.path.split("/")[3].split("?")[0]
            if agent not in NAMES:
                self.send_error(404); return
            body, ctype = json.dumps(school(agent)).encode(), "application/json"
        elif self.path == "/api/apps":
            body, ctype = json.dumps(apps_status()).encode(), "application/json"
        elif self.path.startswith("/api/kb/"):
            # Joshua and Open WebUI's tool send X-Crew; web pages can't, so they can't read Rabbid's notes.
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            what = urlparse(self.path).path.rsplit("/", 1)[1]
            q = parse_qs(urlparse(self.path).query).get("q", [""])[0][:400]
            try:
                if what == "library": result = kb.library(q)
                elif what == "notes": result = kb.notes(q)
                elif what == "news": result = kb.news(q)
                elif what == "command": result = kb.command(q)
                elif what == "now": result = {"now": kb.now()}
                elif what == "calc": result = {"expression": q, "answer": kb.calc(q)}
                else:
                    self.send_error(404); return
            except Exception as e:
                result = {"error": str(e)}
            body, ctype = json.dumps(result).encode(), "application/json"
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if self.path == "/api/lab/upload":
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            dest = lab.upload_path(unquote(self.headers.get("X-Filename", "upload")))
            left = length
            with dest.open("wb") as fh:
                while left > 0:
                    chunk = self.rfile.read(min(1 << 20, left))
                    if not chunk:
                        break
                    fh.write(chunk)
                    left -= len(chunk)
            self._json(lab.submit(self.headers.get("X-Tool", ""), unquote(self.headers.get("X-Text", "")), str(dest)))
            return
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self.send_error(400); return
        if self.path in ("/api/lab/run", "/api/lab/open") and self.headers.get("X-Crew") != "1":
            self.send_error(403); return
        if self.path == "/api/lab/run":
            self._json(lab.submit(data.get("tool", ""), data.get("text", ""))); return
        if self.path == "/api/lab/open":
            self._json({"ok": lab.open_folder(data.get("path", ""))}); return
        if self.path == "/api/search-adapter":
            # Octop's "searchfree" tool, pointed at Rabbid's own SearXNG instead of a third-party site.
            from urllib.parse import quote_plus
            q = str(data.get("query", ""))[:400]
            n = max(1, min(int(data.get("max_results") or 5), 10))
            # Offline library first (works with no internet), then the web. Library only: Octop never sees Rabbid's notes.
            results = []
            try:
                for a in kb.library(q, articles=2, chars=1500)["results"]:
                    results.append({"title": f"{a['title']} (offline {a['source']})", "url": "http://127.0.0.1:8090/",
                                    "snippet": a["text"]})
            except Exception:
                pass
            try:
                raw = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8888/search?q={quote_plus(q)}&format=json", timeout=25).read())
                results += [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")} for r in raw.get("results", [])[:n]]
            except Exception as e:
                if not results:
                    q = f"{q} (search failed: {e})"
            self._json({"query": q, "results": results}); return
        if self.path.startswith("/api/crew-update/") or self.path == "/api/crew-action":
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            if self.path == "/api/crew-action":
                self._json(crew_action(str(data.get("action", "")), str(data.get("text", "")))); return
            agent = self.path.rsplit("/", 1)[1]
            threading.Thread(target=crew_update, args=(agent,), daemon=True).start()
            self._json({"ok": True}); return
        if self.path in ("/api/feedback", "/api/teach", "/api/forget"):
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            agent = str(data.get("agent", ""))
            if agent not in NAMES:
                self._json({"ok": False, "note": "Unknown crew member."}); return
            name, text = NAMES[agent][0], str(data.get("text", "")).strip()[:300]
            if self.path == "/api/feedback":
                had = lessons.add_feedback(agent, bool(data.get("good")), text)
                note = ("👍 Noted. Keep it up." if data.get("good") else
                        f"👎 Noted. {name} will study it tonight and try a fix." if had else
                        f"👎 Noted, but {name} hasn't done a job yet this week to fix.")
                self._json({"ok": True, "note": note}); return
            if self.path == "/api/teach":
                ok = lessons.add(agent, name, "From Rabbid", text, why=f"Rabbid taught: {text}")
                self._json({"ok": ok, "note": f"🎓 {name} learned it." if ok else "Nothing new to learn there."}); return
            gone = lessons.forget(agent, name, text)
            self._json({"ok": bool(gone), "note": f"🗑 Forgot: {gone}" if gone else "No lesson matched."}); return
        if self.path == "/api/think":
            # n8n's crew jobs: free cloud brains via the brain switch, the member's own local model offline.
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            job = str(data.get("job") or "free-chat")
            job = job if job in ("free-chat", "free-smart", "free-coder", "free-long") else "free-chat"
            try:
                system = str(data.get("system", ""))
                out = brain_json(system, str(data.get("user", "")), str(data.get("model") or "llama3.2:3b"),
                                 timeout=900, job=job, agent=str(data.get("agent") or "") or who_is(system))
                self._json({"message": {"content": out}})
            except Exception as e:
                self._json({"message": {"content": json.dumps({"report": f"The free AIs didn't answer ({e}).", "say": "", "alert": True})}})
            return
        if self.path == "/api/free-ask":
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            job = str(data.get("job") or "chat")
            job = job if job in ("chat", "smart", "coder", "long") else "chat"
            try:
                import importlib.machinery
                fa = importlib.machinery.SourceFileLoader("free_ai", str(HOME / ".local/bin/free-ai")).load_module()
                self._json({"answer": fa.ask(str(data.get("text", ""))[:20000], job)})
            except Exception as e:
                self._json({"error": f"The free AIs didn't answer ({e})."})
            return
        if self.path == "/api/rick-update":
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            threading.Thread(target=rick_update, daemon=True).start()
            self._json({"ok": True}); return
        if self.path == "/api/launch/claude":
            # Only Mission Control's own page sends this header; other websites can't (browser blocks it).
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            question = str(data.get("text") or "").strip()[:4000]
            to_empty_workspace()
            subprocess.Popen(["omarchy-launch-tui", "--app-id=org.omarchy.claude", str(HOME / ".local/bin/claude-desk")] + ([question] if question else []),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            result = {"ok": True}
        elif self.path == "/api/launch/openwebui":
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            to_empty_workspace()
            subprocess.Popen(["omarchy-launch-or-focus-webapp", "Rick's Lab", "http://127.0.0.1:3080/"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            result = {"ok": True}
        elif self.path == "/api/launch/claude-desktop":
            if self.headers.get("X-Crew") != "1":
                self.send_error(403); return
            # The app is single-instance: if it's already open this just brings it forward.
            to_empty_workspace()
            subprocess.Popen(["claude-desktop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            result = {"ok": True}
        elif self.path.startswith("/api/deliver/"):
            result = deliver(self.path.split("/")[3], data)
        elif self.path == "/api/inbox":
            with INBOX.open("a") as fh:
                fh.write(f"- {data.get('text', '').strip()} _({time.strftime('%b %-d, %Y')})_\n")
            result = {"ok": True}
        else:
            self.send_error(404); return
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8899), Handler).serve_forever()
