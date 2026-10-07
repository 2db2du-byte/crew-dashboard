# Mission Control (crew dashboard) 🛸

A Rick and Morty themed dashboard for a home AI setup, served by one small Python program (`server.py`, no
dependencies beyond Python 3). It shows a "crew" of AI helpers, each with a job (backups, home lab, notes, devices,
Linux lessons...), their latest reports, a launch pad for your self-hosted apps, a Claude plan meter, and an
"AI Lab" for running free local AI tools.

It also serves a small **crew API** on `127.0.0.1:8899` that other tools use:

| Endpoint | What it does |
|---|---|
| `GET /api/kb/library?q=` | searches an offline [Kiwix](https://kiwix.org) library (Wikipedia etc.) and returns the most relevant passages (`kb.py`) |
| `GET /api/kb/notes?q=` | searches your Obsidian notes (needs Ollama's `nomic-embed-text`) |
| `GET /api/kb/news`, `/command`, `/now`, `/calc` | news feeds (FreshRSS), tldr command help, time, exact math |
| `POST /api/think` | one AI answer: free cloud models through a LiteLLM "brain switch" when online, a local Ollama model when offline |
| `POST /api/deliver/<member>` | files a crew report in today's daily note, pops a notification, can speak it |

Requests that read private data must send the header `X-Crew: 1` (web pages from other sites can't).

**Files:** `server.py` (dashboard + API), `index.html` / `avatars.js` / `pixel.js` (the page, cartoon avatars, a pixel-art
mode), `kb.py` (offline knowledge), `lab.py` (AI Lab tools), `free_ai_bridge.py` (OpenAI-style "auto" model that picks the
best free brain), `openwebui_tool.py` (an [Open WebUI](https://openwebui.com) tool that gives chats the same knowledge).

## Using it

1. `python3 server.py`, then open http://127.0.0.1:8899
2. It was built for one machine (Arch Linux / [Omarchy](https://omarchy.org), an external drive mounted under
   `/run/media/$USER/OmarchyExt1`, an Obsidian vault in `~/SecondBrain`). Paths, crew members and apps are plain
   constants near the top of `server.py`, `kb.py` and `lab.py`; change them to match yours. Missing pieces just show as "off".
3. Pairs with the [crew](../../../crew) repo (n8n jobs + the brain switch) and [hey-joshua](../../../hey-joshua) (voice).

## License

MIT. Built by Rabbid Raccoon with Claude. Use it, change it, share it.
