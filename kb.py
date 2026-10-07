"""Knowledge for the free AIs: Rabbid's offline library (Kiwix), his SecondBrain notes, the time, and math.

Used by Joshua and by Open WebUI's "Rabbid's Knowledge" tool through Mission Control's /api/kb/* endpoints.
Everything is local: Kiwix on 127.0.0.1:8090, embeddings from Ollama's nomic-embed-text.
"""
import ast, html, json, math, operator, re, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
MOUNTS = "/run/media/" + __import__("os").environ.get("USER", "user")  # where removable drives mount

KIWIX = "http://127.0.0.1:8090"
OLLAMA = "http://127.0.0.1:11434"
NOTES = Path.home() / "SecondBrain"
INDEX = Path.home() / ".cache/crew-brain/notes-index.json"
STOP = set("work works working a an the is are was were be to of in on for and or what whats what's who how why when where which do does did "
           "can could would should tell me about explain i you my your it its this that with please hey joshua make makes made thing things".split())


def _get(url, timeout=30):
    return urllib.request.urlopen(url, timeout=timeout).read().decode("utf-8", "replace")


# ---------- offline library ----------
# Video collections are for Rabbid to watch; the AIs can't read them, so don't spend search time on them.
VIDEO_BOOKS = ("khanacademy", "crashcourse", "canadian-prepper", "lrnselfreliance", "urban-prepper")


def _books():
    xml = _get(f"{KIWIX}/catalog/v2/entries?count=500", 15)
    return [b for b in re.findall(r'href="/content/([^"/]+)"', xml) if not b.startswith(VIDEO_BOOKS)]


def _keywords(q):
    words = [w for w in re.findall(r"[a-z0-9'-]+", q.lower()) if w not in STOP]
    return " ".join(words) or q


def _parse_hits(xml):
    out = []
    for rank, item in enumerate(re.findall(r"<item>(.*?)</item>", xml, re.S)):
        title = html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<title>(.*?)</title>", item, re.S).group(1))).strip()
        link = html.unescape(re.search(r"<link>(.*?)</link>", item).group(1))
        book = (re.search(r"^/content/([^/]+)/", link) or [None, ""])[1]
        words = int(re.sub(r"\D", "", (re.search(r"<wordCount>(.*?)</wordCount>", item) or [0, "0"])[1]) or 0)
        out.append({"title": title, "link": link, "book": book, "words": words, "rank": rank})
    return out


def _search_all(q, n=30):
    """ONE full-text search across every English book (142 separate searches swamped Kiwix and the disk)."""
    # Kiwix crashes (HTTP 500) building the snippet of certain results, so a long page of results can fail where a
    # shorter one works: step down until it answers.
    for size in (n, 10, 5):
        try:
            return _parse_hits(_get(f"{KIWIX}/search?pattern={quote(q)}&books.filter.lang=eng&format=xml&pageLength={size}", 20))
        except urllib.error.HTTPError:
            continue
    return []


def _page_text(link):
    """An article's readable paragraphs (falls back to the page's plain text when it has no <p> tags)."""
    page = _get(KIWIX + link, 15)
    page = re.sub(r"(?is)<(script|style|table|sup|figure|nav|header|footer)[^>]*>.*?</\1>", " ", page)
    paras = [html.unescape(re.sub(r"<[^>]+>", " ", p)) for p in re.findall(r"(?is)<(?:p|li|dd)[^>]*>(.*?)</(?:p|li|dd)>", page)]
    if sum(len(p) for p in paras) < 300:
        body = re.sub(r"(?is)<br\s*/?>|</(div|h\d|tr)>", "\n", page)
        paras = [html.unescape(re.sub(r"<[^>]+>", " ", body))]
        paras = paras[0].split("\n")
    out = []
    for p in paras:
        p = re.sub(r"\[\d+\]", "", re.sub(r"\s+", " ", p)).strip()
        if len(p) > 40 and not re.search(r"official website|\.gov website|cookies|javascript", p, re.I):
            out.append(p)
    return out


def _article_text(link, limit):
    return "\n".join(_page_text(link))[:limit]


def _stem(w):
    return w[:5] if len(w) > 5 else w


def _singular(w):
    if w.endswith("ies") and len(w) > 4: return w[:-3] + "y"
    if w.endswith(("ches", "shes", "sses", "xes")): return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3: return w[:-1]
    return w


def _best_passages(paras, kw, chars, lead):
    """The paragraphs that actually talk about the question, kept in reading order (plus the intro for encyclopedias)."""
    stems = {_stem(_singular(w)) for w in kw.split()}
    scored = []
    for i, p in enumerate(paras):
        words = {_stem(_singular(w)) for w in re.findall(r"[a-z0-9'-]+", p.lower())}
        hits = len(stems & words)
        scored.append((hits / max(1, len(stems)) + (0.6 if lead and i == 0 else 0) - (0.15 if len(p) < 120 else 0), i))
    keep, total = set(), 0
    for score, i in sorted(scored, reverse=True):
        if score <= 0 and keep:
            break
        if total + len(paras[i]) > chars and keep:
            continue
        keep.add(i); total += len(paras[i])
        if total >= chars:
            break
    out, last = [], -2
    for i in sorted(keep):
        if out and i != last + 1:
            out.append("…")
        out.append(paras[i][: max(200, chars - sum(len(x) for x in out))])
        last = i
    return "\n".join(out)[:chars]


def _titles(book, term, n=5):
    """Kiwix's title index (fast): articles whose title starts with the words."""
    r = json.loads(_get(f"{KIWIX}/suggest?content={book}&term={quote(term)}&count={n}", 10))
    return [{"title": html.unescape(i["value"]), "link": f"/content/{book}/{i['path']}", "book": book, "words": 9999, "rank": 0}
            for i in r if i.get("kind") == "path" and "disambiguation" not in i["value"].lower()]


def _title_candidates(books, kw):
    """Encyclopedia articles whose title is exactly a word or phrase from the question ("bee sting", "raccoon")."""
    words = [_singular(w) for w in kw.split()]
    spans = {" ".join(words[i:i + n]) for n in (3, 2, 1) for i in range(len(words) - n + 1)}
    spans = [sp for sp in spans if len(sp) >= 3]
    main = [b for b in books if b.startswith(("wikipedia", "mdwiki"))]
    from concurrent.futures import wait
    pool = ThreadPoolExecutor(max_workers=8)
    jobs = [pool.submit(_titles, b, sp, 6) for b in main for sp in spans]
    done, _ = wait(jobs, timeout=10)              # a slow lookup is skipped, not fatal
    pool.shutdown(wait=False, cancel_futures=True)
    out = []
    for j in done:
        try:
            # Exact name only, and not an acronym or oddly-capitalised page ("MATCH", "SMart") for a plain word.
            out += [t for t in j.result() if t["title"].lower() in spans
                    and not any(re.search(r"[A-Z]", w[1:]) for w in t["title"].split())]
        except Exception:
            pass
    return out


JUNK_TITLE = re.compile(r"^(user |users/|highest voted|newest |questions/tagged|tagged )", re.I)
HATNOTE = re.compile(r"^(for other uses|for [^.]{0,120}, see |this article is about|.{0,60} redirects here|not to be confused|see also|main article|↑|\^)", re.I)


def library(q, articles=3, chars=2500):
    """Search the whole offline library; return the most relevant passages from the best few articles.

    One combined full-text search (all books) runs alongside an encyclopedia title lookup. Every candidate article is
    read, ranked by how much of the WHOLE question it covers (rare words count more), and only the paragraphs that
    match the question are kept, so the AIs get the useful part of a long article. `chars` = budget per article.
    """
    kw = _keywords(q)
    try:
        books = _books()
    except Exception as e:
        return {"query": kw, "error": f"Offline Library is off ({e})", "results": []}
    pool = ThreadPoolExecutor(max_workers=12)
    full = pool.submit(_search_all, kw)
    titled = pool.submit(_title_candidates, books, kw)
    hits, exact = [], []
    try:
        exact = titled.result(timeout=14)
    except Exception:
        pass
    try:
        hits = full.result(timeout=22)
    except Exception:
        pass
    hits = [h for h in hits if h["book"] and not h["book"].startswith(VIDEO_BOOKS)
            and "disambiguation" not in h["title"].lower() and not JUNK_TITLE.match(h["title"])]
    for e in exact:
        e["exact"] = True               # the article IS about a thing the question names
    seen, cands = set(), []
    for h in exact + hits[:10]:
        key = re.sub(r"\W", "", h["title"].lower()) + h["book"][:6]
        if key not in seen:
            seen.add(key); cands.append(h)

    def read(h):
        try:
            paras = [p for p in _page_text(h["link"]) if not HATNOTE.match(p)]
            return h, paras
        except Exception:
            return h, []
    from concurrent.futures import wait
    jobs = [pool.submit(read, h) for h in cands]
    done, _ = wait(jobs, timeout=15)              # one slow page is skipped instead of losing them all
    pages = [j.result() for j in jobs if j in done]
    pool.shutdown(wait=False, cancel_futures=True)

    terms = {_stem(_singular(w)): len(w) for w in kw.split()}      # longer words are rarer: weight by length
    total = sum(terms.values()) or 1

    def score(h, paras):
        body = " ".join(paras[:200]).lower()
        if not paras or "may refer to" in " ".join(paras[:2]).lower():
            return -9
        words = {_stem(_singular(w)) for w in re.findall(r"[a-z0-9'-]+", body)}
        title = {_stem(_singular(w)) for w in re.findall(r"[a-z0-9'-]+", h["title"].lower())}
        cover = sum(wt for t, wt in terms.items() if t in words) / total
        named = sum(wt for t, wt in terms.items() if t in title) / total
        return (2 * cover + 1.2 * named + (0.3 if h["book"].startswith(("wikipedia", "mdwiki")) else 0)
                + 0.3 / (h["rank"] + 1) - (0.6 if len(body) < 400 else 0)
                + (0.5 if h.get("exact") else 0) + min(0.3, len(paras) / 300))
    ranked = sorted(((score(h, paras), h, paras) for h, paras in pages), key=lambda x: x[0], reverse=True)
    if __import__("os").environ.get("KB_DEBUG"):
        print("\n".join(f"{sc:.2f} {h['book'][:10]} {h['title']} paras={len(p)}" for sc, h, p in ranked))
    results = []
    for sc, h, paras in ranked:
        if sc < 0.8 or len(results) >= articles:
            break
        text = _best_passages(paras, kw, chars, lead=h["book"].startswith(("wikipedia", "mdwiki", "wikem", "wikibooks")))
        if len(text) > 150 and not any(text[:150] == r["text"][:150] for r in results):   # same page under two names
            results.append({"title": h["title"], "source": h["book"].split("_")[0], "text": text})
    return {"query": kw, "results": results}


# ---------- Rabbid's notes ----------
_lock = threading.Lock()


def _embed(texts):
    body = json.dumps({"model": "nomic-embed-text", "input": texts}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/embed", body, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))["embeddings"]


def _chunks(path):
    text = path.read_text(errors="replace")
    parts, cur = [], ""
    for block in re.split(r"\n(?=#)|\n\n", text):
        if len(cur) + len(block) > 1200 and cur:
            parts.append(cur); cur = ""
        cur += block + "\n\n"
    if cur.strip():
        parts.append(cur)
    return [p.strip()[:1500] for p in parts if p.strip()]


def _index():
    """Notes index, rebuilt only for notes that changed since last time."""
    with _lock:
        old = json.loads(INDEX.read_text()) if INDEX.exists() else {}
        new, changed = {}, False
        for p in NOTES.rglob("*.md"):
            if any(part.startswith(".") for part in p.relative_to(NOTES).parts) or "Templates" in p.parts:
                continue
            key, mtime = str(p.relative_to(NOTES)), p.stat().st_mtime
            if key in old and old[key]["mtime"] == mtime:
                new[key] = old[key]; continue
            chunks = _chunks(p)
            new[key] = {"mtime": mtime, "chunks": chunks, "vecs": _embed([f"search_document: {key}\n{c}" for c in chunks]) if chunks else []}
            changed = True
        if changed or len(new) != len(old):
            INDEX.parent.mkdir(parents=True, exist_ok=True)
            INDEX.write_text(json.dumps(new))
        return new


def notes(q, k=4):
    idx = _index()
    qv = _embed([f"search_query: {q}"])[0]
    qn = math.sqrt(sum(x * x for x in qv))
    scored = []
    for name, d in idx.items():
        for c, v in zip(d["chunks"], d["vecs"]):
            s = sum(a * b for a, b in zip(qv, v)) / (qn * math.sqrt(sum(x * x for x in v)) or 1)
            scored.append((s, name, c))
    scored.sort(reverse=True)
    return {"query": q, "results": [{"note": n.removesuffix(".md"), "score": round(s, 3), "text": c} for s, n, c in scored[:k]]}


# ---------- news (Rabbid's FreshRSS feeds) ----------
NEWS_INDEX = Path.home() / ".cache/crew-brain/news-index.json"
NEWS_DAYS = 30
_EXPORT = r"""
$d = new PDO("sqlite:/var/www/FreshRSS/data/users/admin/db.sqlite");
$q = $d->prepare("select e.id, e.title, e.link, e.date, e.content, f.name feed from entry e join feed f on f.id = e.id_feed where e.date > ?");
$q->execute([time() - %d * 86400]);
$out = [];
foreach ($q as $r) {
  $t = trim(preg_replace("/\s+/", " ", html_entity_decode(strip_tags($r["content"]), ENT_QUOTES)));
  $out[] = ["id" => (string)$r["id"], "title" => html_entity_decode($r["title"], ENT_QUOTES), "link" => $r["link"],
            "date" => (int)$r["date"], "feed" => html_entity_decode($r["feed"], ENT_QUOTES), "text" => mb_substr($t, 0, 1200)];
}
echo json_encode($out);
""" % NEWS_DAYS
_news_lock = threading.Lock()


def _news_index():
    """Articles from the last 30 days, embedded once each. FreshRSS's database is only readable inside its container."""
    import subprocess
    with _news_lock:
        idx = json.loads(NEWS_INDEX.read_text()) if NEWS_INDEX.exists() else {}
        raw = subprocess.run(["docker", "exec", "app-freshrss", "php", "-r", _EXPORT], capture_output=True, text=True, timeout=60).stdout
        arts = {a["id"]: a for a in json.loads(raw or "[]")}
        new = [a for i, a in arts.items() if i not in idx]
        for i in range(0, len(new), 32):
            batch = new[i:i + 32]
            vecs = _embed([f"search_document: {a['title']}\n{a['text'][:800]}" for a in batch])
            for a, v in zip(batch, vecs):
                idx[a["id"]] = a | {"vec": v}
        idx = {i: a for i, a in idx.items() if i in arts}  # older than 30 days drops out
        NEWS_INDEX.parent.mkdir(parents=True, exist_ok=True)
        NEWS_INDEX.write_text(json.dumps(idx))
        return idx


def news(q, k=5):
    idx = _news_index()
    if not idx:
        return {"query": q, "results": []}
    qv = _embed([f"search_query: {q}"])[0]
    qn = math.sqrt(sum(x * x for x in qv))
    scored = sorted(((sum(a * b for a, b in zip(qv, d["vec"])) / (qn * math.sqrt(sum(x * x for x in d["vec"])) or 1), d)
                     for d in idx.values()), key=lambda t: t[0], reverse=True)
    return {"query": q, "results": [{"title": d["title"], "feed": d["feed"], "score": round(s, 3),
                                     "date": time.strftime("%a %b %-d", time.localtime(d["date"])), "link": d["link"],
                                     "text": d["text"]} for s, d in scored[:k]]}


# ---------- Linux command cheat sheets (tldr pages) ----------
TLDR = Path(MOUNTS + "/OmarchyExt1/Offline Library/tldr (command cheat sheets)/pages")
# Everyday words that also happen to be command names; only count them in a pair ("git commit").
NOT_COMMANDS = {"file", "time", "date", "use", "help", "make", "open", "look", "more", "less", "last", "write", "test",
                "true", "false", "yes", "w", "at", "watch", "join", "split", "sort", "head", "tail", "top", "kill", "wall"}


def command(q, k=2):
    """Plain-English examples for terminal commands mentioned in q ("how do I use tar", "git commit")."""
    words = re.findall(r"[a-z0-9][a-z0-9.+_-]*", q.lower())
    names = [f"{a}-{b}" for a, b in zip(words, words[1:])] + words  # "git commit" -> git-commit first
    out, seen = [], set()
    for n in names:
        for section in ("linux", "common"):
            f = TLDR / section / f"{n}.md"
            if f.exists() and n not in seen and n not in STOP and (n not in NOT_COMMANDS or len(words) <= 2):
                seen.add(n)
                out.append({"command": n.replace("-", " ") if "-" in n and n.split("-")[0] in words else n,
                            "text": f.read_text()[:2500]})
                break
        if len(out) >= k:
            break
    return {"query": q, "results": out}


# ---------- time and math ----------
def now():
    return time.strftime("It is %-I:%M %p on %A, %B %-d, %Y.")


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv, ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {n: getattr(math, n) for n in ("sqrt", "sin", "cos", "tan", "log", "log10", "exp", "floor", "ceil")} | {"abs": abs, "round": round}


def calc(expr):
    """Safe calculator: numbers, + - * / ** % //, parentheses, sqrt/log/sin/... and pi, e."""
    expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/")

    def ev(n):
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
        if isinstance(n, ast.Name) and n.id in ("pi", "e"): return getattr(math, n.id)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            if isinstance(n.op, ast.Pow) and abs(ev(n.right)) > 1000: raise ValueError("exponent too big")
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS: return _OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS:
            return _FUNCS[n.func.id](*[ev(a) for a in n.args])
        raise ValueError("not plain math")
    r = ev(ast.parse(expr, mode="eval"))
    return int(r) if isinstance(r, float) and r.is_integer() and abs(r) < 1e15 else round(r, 6) if isinstance(r, float) else r
