r"""AutoEdit - builds a finished CapCut timeline straight from a content folder.

    python autoedit.py "<content folder>" --project "<CapCut project name>"

Content folder:  Pictures\ (0001_*.jpg ...), Voice\ (Script 1.mp3 ...), and the scene-by-scene guide (.md).
CapCut must be CLOSED. See GUIDE.md for everything else.
"""
import argparse, copy, difflib, glob, json, math, os, random, re, shutil, subprocess, sys, time, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
YTA = os.path.dirname(HERE)
CAPCUT_ROOT = os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft")
US, FPS = 1_000_000, 30
FRAME = US / FPS
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
AUD_EXT = (".mp3", ".wav", ".m4a", ".aac")
WARN = []

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def log(*a):
    print(*a, flush=True)


def warn(msg):
    WARN.append(msg)
    log("  ! " + msg)


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def jsave(p, obj, pretty=False):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, **({"indent": 1} if pretty else {"separators": (",", ":")}))


def nid():
    u = str(uuid.uuid4()).upper()
    return u[:14] + u[14:19].lower() + u[19:]


def fr(t):
    return int(round(t * FPS) * US / FPS)


def lib_path(p):
    return p if os.path.isabs(p) else os.path.join(YTA, p)


def deep_merge(a, b):
    for k, v in b.items():
        a[k] = deep_merge(a.get(k, {}), v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return a


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


# ============================================================ text normalisation
def norm(s):
    s = s.lower().replace("’", "'").replace("–", " ").replace("—", " ").replace("-", " ")
    s = re.sub(r"(?<=\d),(?=\d)", "", s)
    return [t for t in re.sub(r"[^\w' ]|_", " ", s).split() if t.strip("'")]


# ============================================================ content discovery
def find_content(folder):
    if not os.path.isdir(folder):
        sys.exit(f"Content folder not found: {folder}")
    sub = {d.lower(): os.path.join(folder, d) for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))}
    pics = next((sub[n] for n in ("pictures", "picture", "images", "image") if n in sub), None)
    if not pics:
        sys.exit("No Pictures folder found (expected <content>\\Pictures).")
    images = {}
    for f in sorted(os.listdir(pics), key=natural_key):
        m = re.match(r"^(\d+)", f)
        if m and f.lower().endswith(IMG_EXT):
            images.setdefault(int(m.group(1)), os.path.join(pics, f).replace("\\", "/"))
    vdir = next((sub[n] for n in ("voice", "voice over", "voiceover", "vo", "audio") if n in sub), folder)
    voice = sorted([os.path.join(vdir, f).replace("\\", "/") for f in os.listdir(vdir)
                    if f.lower().endswith(AUD_EXT) and (vdir != folder or f.lower().startswith("script"))],
                   key=lambda p: natural_key(os.path.basename(p)))
    if not voice:
        sys.exit("No voice files found (expected <content>\\Voice\\Script 1.mp3, Script 2.mp3 ...).")
    guides = [g for g in glob.glob(os.path.join(folder, "*.md"))
              if re.search(r"^#+\s*Beat\s+\d+", open(g, encoding="utf-8", errors="ignore").read(), re.M)]
    if not guides:
        sys.exit("No scene-by-scene guide (.md with '### Beat 1' headings) found in the content folder.")
    guides.sort(key=lambda g: ("prompt" not in g.lower() and "scene" not in g.lower(), g))
    extra_sfx = next((sub[n] for n in ("sfx", "sound effects", "sounds") if n in sub), None)
    return {"pictures": pics, "images": images, "voice": voice, "guide": guides[0], "extra_sfx_dir": extra_sfx}


def parse_guide(path):
    txt = open(path, encoding="utf-8").read()
    title = None
    m = re.search(r'^#+\s*["“](.+?)["”]\s*$', txt, re.M)
    if m:
        title = m.group(1).strip()
    beats, sec, sections = [], (0, ""), {}
    for line in txt.splitlines():
        m = re.match(r"^#+\s*SECTION\s+(\d+)\s*[:.\-–]\s*(.+?)\s*(\(.*)?$", line, re.I)
        if m:
            sec = (int(m.group(1)), m.group(2).strip())
            est = re.search(r"(\d+):(\d+(?:\.\d+)?)", m.group(3) or "")  # "(Beats 4–5, 0:48.8–1:15.6)" -> 48.8
            sections[sec[0]] = {"name": sec[1], "est": int(est[1]) * 60 + float(est[2]) if est else None}
            continue
        # Match beat header with optional timing: "### Beat 180 — 11:56–12:00"
        m = re.match(r"^#+\s*Beat\s+(\d+)(?:\s*[—–-]\s*(\d{1,2}:\d{2})[—–-](\d{1,2}:\d{2}))?", line, re.I)
        if m:
            beat_timing = None
            if m.group(2) and m.group(3):
                # Convert MM:SS to seconds
                def ts_to_sec(ts):
                    parts = ts.strip().split(":")
                    if len(parts) == 2:
                        return int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 3:
                        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    return None
                start_s = ts_to_sec(m.group(2))
                end_s = ts_to_sec(m.group(3))
                if start_s is not None and end_s is not None and end_s > start_s:
                    beat_timing = (start_s, end_s)
            beats.append({"n": int(m.group(1)), "sec": sec, "text": "", "action": "", "mood": "", "timing": beat_timing})
            continue
        if not beats:
            continue
        m = re.match(r'^\**\s*Script Segment:?\**:?\s*["“]?(.*?)["”]?\s*$', line, re.I)
        if m and not beats[-1]["text"]:
            beats[-1]["text"] = m.group(1).strip()
        m = re.match(r"^\s*[-*]\s*\**Action:?\**:?\s*(.*)$", line, re.I)
        if m:
            beats[-1]["action"] = m.group(1).strip()
        m = re.match(r"^\s*[-*]\s*\**Mood:?\**:?\s*(.*)$", line, re.I)
        if m:
            beats[-1]["mood"] = m.group(1).strip()
    beats = [b for b in beats if b["text"]]
    if not beats:
        sys.exit("Guide has no 'Script Segment' lines.")
    if all(b["sec"][0] == 0 for b in beats):
        for b in beats:
            b["sec"] = (1 + (b["n"] - 1) // 12, "")
            sections.setdefault(b["sec"][0], {"name": f"Part {b['sec'][0]}", "est": None})
    return title, beats, sections


# ============================================================ audio analysis
_AV = None


def av():
    global _AV
    if _AV is None:
        import av as _av
        _AV = _av
    return _AV


def media_dur_us(path):
    c = av().open(path)
    d = int(c.duration)
    c.close()
    return d


def analyse_audio(path, cache):
    key = os.path.normcase(os.path.abspath(path))
    st = os.stat(path)
    hit = cache.get(key)
    if hit and hit["size"] == st.st_size and abs(hit["mtime"] - st.st_mtime) < 1:
        return hit
    import numpy as np
    c = av().open(path)
    r = av().AudioResampler(format="flt", layout="mono", rate=22050)
    peak, chunks = 0.0, []
    for f in c.decode(audio=0):
        a = f.to_ndarray()
        peak = max(peak, float(np.abs(a).max()) if a.size else 0.0)
        for g in r.resample(f):
            chunks.append(g.to_ndarray().ravel())
    c.close()
    x = np.concatenate(chunks)
    win = int(0.05 * 22050)
    n = max(1, len(x) // win)
    db = 20 * np.log10(np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(1) + 1e-12))
    act = db[db > db.max() - 30]
    res = {"size": st.st_size, "mtime": st.st_mtime,
           "active_db": float(10 * np.log10((10 ** (act / 10)).mean())),
           "peak_db": float(db.max()), "peak_t": float(db.argmax() * 0.05),
           "sample_peak_db": float(20 * math.log10(peak + 1e-12))}
    cache[key] = res
    return res


# ============================================================ transcription + alignment
def transcribe(voice, work, model_name, force):
    tdir = os.path.join(work, "transcripts")
    os.makedirs(tdir, exist_ok=True)
    out, model = [], None
    for p in voice:
        cp = os.path.join(tdir, os.path.basename(p) + ".json")
        st = os.stat(p)
        if not force and os.path.exists(cp):
            c = jload(cp)
            if c.get("size") == st.st_size and c.get("model") == model_name:
                out.append(c["words"])
                continue
        if model is None:
            log(f"Loading speech model '{model_name}' (first time downloads it)...")
            from faster_whisper import WhisperModel
            model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
        log(f"Transcribing {os.path.basename(p)} (a few minutes on CPU)...")
        segs, _ = model.transcribe(p, language="en", word_timestamps=True, beam_size=5)
        words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
        jsave(cp, {"size": st.st_size, "model": model_name, "words": words}, pretty=True)
        out.append(words)
    return out


def align(beats, per_file_words, durs_s, lead):
    words, off = [], 0.0
    for fw, d in zip(per_file_words, durs_s):
        for x in fw:
            for t in norm(x["w"]):
                words.append({"t": t, "s": x["s"] + off, "e": x["e"] + off})
        off += d
    stoks = [(b["n"], t) for b in beats for t in norm(b["text"])]
    sm = difflib.SequenceMatcher(None, [t for _, t in stoks], [w["t"] for w in words], autojunk=False)
    match = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            match[a + k] = b + k
    log(f"Matched {len(match)}/{len(stoks)} script words to the voice-over.")
    if len(match) < 0.6 * len(stoks):
        warn("Less than 60% of the script matched the voice. Is the guide for this voice-over?")
    matched_idx = sorted(match)

    def tok_time(gi):
        if gi in match:
            return words[match[gi]]["s"]
        import bisect
        j = bisect.bisect_left(matched_idx, gi)
        if j == 0:
            return max(0.0, words[match[matched_idx[0]]]["s"] - 0.33 * (matched_idx[0] - gi)) if matched_idx else 0.0
        if j >= len(matched_idx):
            p = matched_idx[-1]
            return min(off, words[match[p]]["e"] + 0.33 * (gi - p))
        p, q = matched_idx[j - 1], matched_idx[j]
        t0, t1 = words[match[p]]["e"], words[match[q]]["s"]
        return t0 + (t1 - t0) * (gi - p) / (q - p)

    first_tok, gi = {}, 0
    for b in beats:
        first_tok[b["n"]] = gi
        b["tok0"], b["tokens"] = gi, norm(b["text"])
        gi += len(b["tokens"])
    for i, b in enumerate(beats):
        idxs = range(b["tok0"], b["tok0"] + len(b["tokens"]))
        hit = next((g for g in idxs if g in match), None)
        b["match_ratio"] = sum(g in match for g in idxs) / max(1, len(b["tokens"]))
        if hit is None:
            b["speech"] = tok_time(b["tok0"])
            b["prev_end"] = None
        else:
            wi = match[hit]
            b["speech"] = words[wi]["s"] - 0.33 * (hit - b["tok0"])
            b["prev_end"] = words[wi - 1]["e"] if wi and hit == b["tok0"] else None
    for i, b in enumerate(beats):
        if i == 0:
            b["cut"] = 0.0
            continue
        # Use explicit start time from beat header if provided
        if b.get("timing"):
            b["cut"] = float(b["timing"][0])
            continue
        pe = b["prev_end"]
        if pe is not None and b["speech"] > pe:
            b["cut"] = max(pe + (b["speech"] - pe) * 0.35, b["speech"] - lead)
        else:
            b["cut"] = b["speech"] - lead
        b["cut"] = max(b["cut"], beats[i - 1]["cut"] + 0.4)
    for i, b in enumerate(beats):
        # Use explicit timing from beat header if provided, otherwise use voice alignment
        if b.get("timing"):
            # Beat header has explicit start-end time (e.g., "11:56–12:00")
            b["end"] = float(b["timing"][1])
        else:
            # Standard behavior: end at next beat's cut, or at voice-over end
            b["end"] = beats[i + 1]["cut"] if i + 1 < len(beats) else off
        if b["match_ratio"] < 0.5:
            warn(f"Beat {b['n']}: only {b['match_ratio']:.0%} of its words were heard - check its timing.")
    return words, tok_time, off


def anchor_time(b, phrase, tok_time, words):
    """Time when `phrase` (script words) is spoken inside beat b."""
    if not phrase:
        return b["cut"] + 0.15
    p = norm(phrase)
    toks = b["tokens"]
    for k in range(len(toks) - len(p) + 1):
        if toks[k:k + len(p)] == p:
            return tok_time(b["tok0"] + k)
    hit = next((w["s"] for w in words if b["cut"] - 0.05 <= w["s"] < b["end"] and w["t"] == p[0]), None)
    if hit is None:
        warn(f"Beat {b['n']}: could not find '{phrase}' in the narration; label placed at the start of the beat.")
        return b["cut"] + 0.15
    return hit


# ============================================================ automatic labels
ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9,
       "tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15,
       "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19, "twentieth": 20, "twenty-first": 21}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
APPROX = re.compile(r"\b(about|around|roughly|approximately|nearly|almost|some|circa)\s+$", re.I)
STOP = {"until", "by", "and", "with", "from", "to", "of", "in", "at", "for", "that", "who", "when", "led", "which", "but",
        "so", "then", "as", "is", "was", "were", "on", "it", "its", "his", "her", "their", "this", "named"}


def ordinal(n):
    return f"{n}{'TH' if 10 <= n % 100 <= 20 else {1: 'ST', 2: 'ND', 3: 'RD'}.get(n % 10, 'TH')}"


def number_label(text):
    pats = [
        (r"(\d[\d,]*)\s*(?:to|-|–)\s*(\d[\d,]*)\s*(BCE|BC|CE|AD)\b", lambda m: f"{m[1]}–{m[2]} {m[3].upper()}"),
        (r"(\d[\d,]*)\s*(BCE|BC|CE|AD)\b", lambda m: f"{m[1]} {m[2].upper()}"),
        (r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand)?", lambda m: f"${m[1]}" + (f" {m[2].upper()}" if m[2] else "")),
        (r"(\d[\d,.]*)\s*(million|billion|thousand)?\s+years?(\s+(?:ago|old))?\b",
         lambda m: f"{m[1]}{' ' + m[2].upper() if m[2] else ''} YEARS{(m[3] or '').upper()}"),
        (r"(\d[\d,.]*)\s*(%|percent)", lambda m: f"{m[1]}%"),
        (r"(\d[\d,.]*)\s*(millimeters?|centimeters?|kilometers?|meters?|miles?|feet|inches|kilograms?|grams?|tons?|pounds?|mm|cm|km|kg)\b",
         lambda m: f"{m[1]} {m[2].upper()}"),
        (r"\b(\d{1,2})(?:st|nd|rd|th)\s+century", lambda m: f"{ordinal(int(m[1]))} CENTURY"),
        (r"\b(" + "|".join(ORD) + r")\s+century", lambda m: f"{ordinal(ORD[m[1].lower()])} CENTURY"),
        (r"\b(1[0-9]{3}|20[0-9]{2})s\b", lambda m: f"THE {m[1]}s"),
        (r"\b((?:" + MONTHS + r")\s+(?:of\s+)?)?(1[0-9]{3}|20[0-9]{2})\b(?!\s*(?:BCE|BC|to|-|–))",
         lambda m: (re.sub(r"\s+of\s+$", " ", m[1]).upper().strip() + " " if m[1] else "") + m[2]),
    ]
    for pat, fmt in pats:
        m = re.search(pat, text, re.I)
        if m:
            lab = fmt(m)
            if APPROX.search(text[: m.start()]):
                lab = "~" + lab
            return lab, m.start()
    return None


def person_names(beats):
    """First appearance of named characters, taken from the guide's image descriptions."""
    seen, out = set(), {}
    name_re = r"[A-Z][\w'’.\-]+(?:\s+(?:[A-Z][\w'’.\-]+|de|van|von|da|del|el|al|bin|ibn|le|la)){1,3}"
    for b in beats:
        for m in re.finditer(r"\(([^():]+):\s*(?:stickman|same) template", b["action"]):
            names = [n.strip() for n in re.split(r",|\band\b", m.group(1)) if n.strip()]
            if len(names) > 1 and all(re.fullmatch(name_re, n) for n in names) and not any(n in seen for n in names):
                seen.update(names)
                out.setdefault(b["n"], ([n.split()[-1].upper() for n in names], names[0], None))
        for m in re.finditer(r"(" + name_re + r")\s*\((?:stickman|same)\s+template", b["action"]):
            n = m.group(1).strip()
            if n in seen or b["n"] in out:
                continue
            seen.add(n)
            out[b["n"]] = (n.upper(), n, role_for(b["text"], n))
    return out


def role_for(text, name):
    i = text.find(name)
    if i < 0:
        return None
    after = re.match(r",\s+(?:an?|the)\s+([^,.;:!?]+)", text[i + len(name):])
    if after and len(after.group(1)) <= 48:
        r = after.group(1).strip()
        return r[0].upper() + r[1:]
    before = text[:i].rstrip()
    if before.endswith(","):
        before = before[:-1]
    clause = re.split(r"[,.;:!?]", before)[-1].split()
    clause = [w for w in clause if w.lower() != "named"]
    while clause and clause[0].lower() in ("the", "a", "an"):
        clause = clause[1:]
    if 1 <= len(clause) <= 3 and not any(w.lower() in STOP for w in clause):
        r = " ".join(clause)
        return r[0].upper() + r[1:]
    return None


def auto_texts(title, beats, cfg):
    A, out, used = cfg["text"]["auto"], [], set()
    title_toks = set(norm(title)) - {"the", "a", "an", "of"} if title else set()
    if A.get("title") and title_toks:
        for b in beats:
            if len(title_toks & set(b["tokens"])) >= 0.8 * len(title_toks) and "?" in b["text"]:
                first = next(t for t in b["tokens"] if t in title_toks)
                out.append({"beat": b["n"], "at": first, "text": title.upper(), "pos": "right"})
                used.add(b["n"])
    if A.get("cta"):
        for b in beats:
            low = b["text"].lower()
            if "like button" in low or re.search(r"\bhit (the )?like\b", low):
                out.append({"beat": b["n"], "at": "like", "text": "HIT THE LIKE BUTTON", "pos": "lower"}); used.add(b["n"])
            elif "subscribe" in low:
                out.append({"beat": b["n"], "at": "subscribe",
                            "text": "SUBSCRIBE & COMMENT" if "comment" in low else "SUBSCRIBE", "pos": "lower"}); used.add(b["n"])
    if A.get("names"):
        for n, (label, raw, role) in person_names(beats).items():
            if n in used:
                continue
            b = next(x for x in beats if x["n"] == n)
            at = raw if raw in b["text"] else None
            text = " · ".join(label) if isinstance(label, list) else label + (f"|{role}" if role else "")
            out.append({"beat": n, "at": at, "text": text, "pos": "lower"}); used.add(n)
    if A.get("numbers"):
        for b in beats:
            if b["n"] in used:
                continue
            r = number_label(b["text"])
            if r:
                lab, pos = r
                k = len(norm(b["text"][:pos]))
                at = " ".join(b["tokens"][k:k + 1]) or None
                out.append({"beat": b["n"], "at": at, "text": lab, "pos": "lower"})
    out.sort(key=lambda e: e["beat"])
    return out


def wrap(text, width, max_lines):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            if cur and len(cur) + 1 + len(w) > width:
                lines.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
    if len(lines) > max_lines:
        warn(f"Label '{text}' needs {len(lines)} lines; consider shortening it in texts.json.")
    return "\n".join(lines)


# ============================================================ CapCut project helpers
def capcut_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"], capture_output=True, text=True).stdout
        return "capcut.exe" in out.lower()
    except Exception:
        return False


def pick_project(name):
    projects = [d for d in os.listdir(CAPCUT_ROOT) if os.path.isfile(os.path.join(CAPCUT_ROOT, d, "draft_content.json"))]
    projects.sort(key=lambda d: os.path.getmtime(os.path.join(CAPCUT_ROOT, d, "draft_content.json")), reverse=True)
    if name:
        exact = [p for p in projects if p.lower() == name.lower()]
        part = [p for p in projects if name.lower() in p.lower()]
        if exact or len(part) == 1:
            return os.path.join(CAPCUT_ROOT, (exact or part)[0])
        log(f"CapCut project '{name}' not found" + (" (several match)" if part else "") + ".")
    log("\nMost recent CapCut projects:")
    for i, p in enumerate(projects[:12], 1):
        log(f"  {i:2d}. {p}")
    ans = input("Type the number of the project to fill (or q to quit): ").strip()
    if not ans.isdigit() or not 1 <= int(ans) <= min(12, len(projects)):
        sys.exit("Cancelled.")
    return os.path.join(CAPCUT_ROOT, projects[int(ans) - 1])


def timeline_dir(proj):
    pj = os.path.join(proj, "Timelines", "project.json")
    if os.path.exists(pj):
        d = os.path.join(proj, "Timelines", jload(pj).get("main_timeline_id", ""))
        if os.path.isdir(d):
            return d
    return None


# ============================================================ build
class Builder:
    def __init__(self, base, T):
        self.d = base
        self.T = T
        self.M = base["materials"]
        for k in self.M:
            self.M[k] = []
        for k in base.get("keyframes", {}):
            base["keyframes"][k] = []
        self.tracks = []

    def mat(self, cat, obj):
        self.M.setdefault(cat, []).append(obj)

    def extras(self, pack):
        ids = []
        for x in pack["extras"]:
            o = copy.deepcopy(x["object"]); o["id"] = nid()
            self.mat(x["category"], o); ids.append(o["id"])
        return ids

    def track(self, ttype):
        t = {"id": nid(), "type": ttype, "flag": 0, "attribute": 0, "name": "", "is_default_name": True, "segments": []}
        self.tracks.append(t)
        return t

    @staticmethod
    def kf(prop, pts):
        return {"id": nid(), "material_id": "", "property_type": prop, "keyframe_list": [
            {"id": nid(), "curveType": "Line", "time_offset": int(t), "left_control": {"x": 0.0, "y": 0.0},
             "right_control": {"x": 0.0, "y": 0.0}, "values": [float(v)], "string_value": "", "graphID": ""} for t, v in pts]}

    def photo(self, track, path, w, h, start_us, dur_us, scale_pts, anim=None):
        P = self.T["video"]
        m = copy.deepcopy(P["material"])
        m.update(id=nid(), unique_id=uuid.uuid4().hex, path=path, material_name=os.path.basename(path), width=w, height=h,
                 local_material_id="", type="photo", duration=10800000000)
        self.mat("videos", m)
        refs = self.extras(P)
        if anim:
            a_obj = next(o for o in self.M["material_animations"] if o["id"] in refs)
            a_obj["animations"] = [anim]
        s = copy.deepcopy(P["segment"])
        s.update(id=nid(), material_id=m["id"], extra_material_refs=refs, render_index=0, track_render_index=0,
                 source_timerange={"start": 0, "duration": dur_us}, target_timerange={"start": start_us, "duration": dur_us},
                 common_keyframes=[self.kf("KFTypeScaleX", scale_pts)], keyframe_refs=[])
        s["clip"]["scale"] = {"x": scale_pts[0][1], "y": scale_pts[0][1]}
        s["clip"]["transform"] = {"x": 0.0, "y": 0.0}
        track["segments"].append(s)

    def audio(self, track, path, pool_id, full_us, start_us, src_us, dur_us, vol, fin=0, fout=0):
        P = self.T["audio"]
        m = copy.deepcopy(P["material"])
        m.update(id=nid(), unique_id=uuid.uuid4().hex, type="extract_music", name=os.path.basename(path), duration=full_us,
                 path=path, category_name="local", music_id=str(uuid.uuid4()), local_material_id=pool_id, wave_points=[],
                 check_flag=1)
        self.mat("audios", m)
        refs = self.extras(P)
        if fin or fout:
            f = {"id": nid(), "type": "audio_fade", "fade_type": 0, "fade_in_duration": int(fin), "fade_out_duration": int(fout)}
            self.mat("audio_fades", f); refs.append(f["id"])
        s = copy.deepcopy(P["segment"])
        s.update(id=nid(), material_id=m["id"], extra_material_refs=refs, volume=float(vol), last_nonzero_volume=float(vol),
                 source_timerange={"start": int(src_us), "duration": int(dur_us)},
                 target_timerange={"start": int(start_us), "duration": int(dur_us)}, render_index=0,
                 track_render_index=self.tracks.index(track), common_keyframes=[], keyframe_refs=[])
        track["segments"].append(s)

    def text(self, track, k, content, start_us, dur_us, x, y, scale, tcfg, font):
        P = self.T["text"]
        parts = [(l + "\n", 15) for l in content["main"].split("\n")]
        if content["sub"]:
            parts += [(content["sub"], 10)]
        else:
            parts[-1] = (parts[-1][0].rstrip("\n"), 15)
        full, styles, pos = "", [], 0
        for p, size in parts:
            styles.append({"fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": tcfg["color"]}}},
                           "font": {"id": tcfg["font_resource_id"], "path": font},
                           "strokes": [{"content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": tcfg["stroke_color"]}},
                                        "width": tcfg["stroke_width"], "mode": 0}],
                           "size": size, "range": [pos, pos + len(p)]})
            pos += len(p); full += p
        m = copy.deepcopy(P["material"])
        m.update(id=nid(), content=json.dumps({"styles": styles, "text": full}, ensure_ascii=False), font_path=font,
                 font_size=15.0, text_color="#FFFFFF", border_color="#000000", border_width=tcfg["stroke_width"],
                 alignment=1, line_max_width=0.82, words={"start_time": [], "end_time": [], "text": []},
                 current_words={"start_time": [], "end_time": [], "text": []})
        if m.get("fonts"):
            m["fonts"] = [dict(m["fonts"][0], id=nid(), path=font)]
        self.mat("texts", m)
        refs = self.extras(P)
        s = copy.deepcopy(P["segment"])
        pop = int(FRAME * 6)
        s.update(id=nid(), material_id=m["id"], extra_material_refs=refs, source_timerange=None,
                 target_timerange={"start": start_us, "duration": dur_us}, render_index=14000 + k, track_render_index=1 + k,
                 keyframe_refs=[], common_keyframes=[
                     self.kf("KFTypeScaleX", [(0, scale * 0.82), (pop, scale)]),
                     self.kf("KFTypeAlpha", [(0, 0.0), (pop, 1.0), (max(pop + 1, dur_us - int(FRAME * 7)), 1.0), (dur_us - int(FRAME), 0.0)])])
        s["clip"] = {"scale": {"x": scale, "y": scale}, "rotation": 0.0, "transform": {"x": x, "y": y},
                     "flip": {"vertical": False, "horizontal": False}, "alpha": 1.0}
        track["segments"].append(s)
        return full


def text_box(full, sizes, scale, x, y, font_path):
    """Generous (worst-case) estimate of the on-screen box in 1920x1080 pixels."""
    from PIL import ImageFont
    f = ImageFont.truetype(font_path, 1000)
    em = 86 / 15
    lines = full.split("\n")
    w = max(f.getlength(l) / 1000 * sz * em * scale for l, sz in zip(lines, sizes))
    h = sum(1.25 * sz * em * scale for sz in sizes)
    cx, cy = (x + 1) / 2 * 1920, (1 - y) / 2 * 1080
    return cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2


def validate(d):
    errs, idx = [], {}
    for k, v in d["materials"].items():
        for x in v:
            if isinstance(x, dict) and "id" in x:
                if x["id"] in idx:
                    errs.append(f"duplicate id {x['id']}")
                idx[x["id"]] = x
    for ti, t in enumerate(d["tracks"]):
        end = 0
        for s in t["segments"]:
            st, du = s["target_timerange"]["start"], s["target_timerange"]["duration"]
            if du <= 0:
                errs.append(f"track {ti}: empty segment at {st / US:.2f}s")
            if st < end:
                errs.append(f"track {ti}: overlap at {st / US:.2f}s")
            if t["type"] == "video" and st != end:
                errs.append(f"video gap at {end / US:.2f}s")
            end = st + du
            for r in [s["material_id"]] + s["extra_material_refs"]:
                if r not in idx:
                    errs.append(f"track {ti}: missing material {r}")
            for k in s.get("common_keyframes") or []:
                for f in k["keyframe_list"]:
                    if not 0 <= f["time_offset"] < du:
                        errs.append(f"track {ti}: keyframe outside clip at {st / US:.2f}s")
            m = idx.get(s["material_id"], {})
            if t["type"] in ("video", "audio") and not os.path.isfile(m.get("path", "")):
                errs.append(f"missing file {m.get('path')}")
    return errs


def mood_of(sec_beats, cfg):
    kw = {k: v for k, v in cfg["music"]["mood_keywords"].items() if not k.startswith("_")}
    title = sec_beats[0]["sec"][1].lower()
    moods = " ".join(sorted({b["mood"].lower() for b in sec_beats}))
    actions = [b["action"].lower() for b in sec_beats]
    score = {}
    for mood, words in kw.items():
        s = 0.0
        for w in words:  # whole words; a trailing * means "any word starting with"
            rx = re.compile(r"\b" + re.escape(w.rstrip("*")) + (r"\w*" if w.endswith("*") else r"\b"))
            s += 3 * bool(rx.search(title)) + 2 * len(rx.findall(moods)) + min(3, sum(bool(rx.search(a)) for a in actions)) * 0.5
        score[mood] = s
    sec_beats[0]["_mood_scores"] = score
    best = max(score.values()) if score else 0
    if best <= 0:
        return cfg["music"]["default_mood"]
    tops = [m for m, s in score.items() if s == best]
    return cfg["music"]["default_mood"] if cfg["music"]["default_mood"] in tops else tops[0]


# ============================================================ YouTube upload text (description / tags / pinned comment)
GENERIC_TAG_WORDS = {"history", "historical", "documentary", "explainer", "explained", "educational", "education", "video",
                     "videos", "channel", "curiosity", "deep", "dive", "how", "things", "were", "was", "invented", "invent",
                     "invention", "inventions", "origin", "origins", "story", "stories", "facts", "fact", "the", "of", "and",
                     "a", "an", "to", "in", "for", "did", "do", "humans", "human", "ancient", "science", "archaeology",
                     "mystery", "mysteries", "why", "what", "who", "when", "first", "real", "truth", "secret", "secrets"}
CREDIT_LINE = re.compile(r"kevin macleod|incompetech|creativecommons\.org|licensed under creative commons", re.I)


def load_credits():
    p = os.path.join(YTA, "Library", "Music", "credits.json")
    return {k: v for k, v in jload(p).items() if not k.startswith("_")} if os.path.exists(p) else {}


def credit_lines(title, reg):
    return reg.get(title) or reg.get(title.lower())


def yt_time(s):
    s = int(s)
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def tag_chars(tags):  # how YouTube counts the 500-character tag limit (tags with spaces get quotes)
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags) - 1)


def find_txt(content, *keys):
    fs = [f for f in glob.glob(os.path.join(content, "*.txt"))
          if any(k in os.path.basename(f).lower() for k in keys) and not os.path.basename(f).upper().startswith("YOUTUBE UPLOAD")]
    return sorted(fs, key=lambda f: len(os.path.basename(f)))[0] if fs else None


def make_upload(content, title, beats, sections, draft, out_dir=None):
    """Write '<content>\\YOUTUBE UPLOAD.txt': description with chapters re-timed to the real edit + music credits,
    tags trimmed to YouTube's limit, pinned comments, and a list of checks. Original .txt files are not changed."""
    ok, todo = [], []
    sec_start = {}
    for b in beats:
        sec_start.setdefault(b["sec"][0], b["cut"])
    end_s = draft["duration"] / US

    # ---- music actually on the timeline (in order of appearance)
    amap = {m["id"]: m for m in draft["materials"].get("audios", [])}
    used = sorted((s["target_timerange"]["start"], os.path.splitext(os.path.basename(amap[s["material_id"]]["path"]))[0])
                  for t in draft["tracks"] if t["type"] == "audio" for s in t["segments"]
                  if s["material_id"] in amap and re.search(r"[\\/]music[\\/]", amap[s["material_id"]]["path"], re.I))
    reg, music = load_credits(), []
    for t in dict.fromkeys(n for _, n in used):
        lines = credit_lines(t, reg)
        if lines:
            music += lines + [""]
        else:
            todo.append(f"No credit text for music '{t}'. Add it to Library\\Music\\credits.json, then run again.")

    # ---- description
    desc_p = find_txt(content, "description")
    lines = open(desc_p, encoding="utf-8-sig").read().splitlines() if desc_p else []
    if not desc_p:
        todo.append("No Description.txt in the content folder - only chapters and music credits were created.")
    ts_re = re.compile(r"^\s*((?:\d{1,2}:)?\d{1,2}:\d{2})\s*[-–—|]?\s*(.+?)\s*$")
    to_s = lambda t: sum(int(p) * 60 ** k for k, p in enumerate(reversed(t.split(":"))))
    est = {n: s["est"] for n, s in sections.items() if s.get("est") is not None}
    chap = []  # [line index or None, new seconds, name, old seconds]
    for i, l in enumerate(lines):
        m = ts_re.match(l)
        if not m:
            continue
        old, name, n = to_s(m[1]), m[2], None
        if old == 0:
            n = min(sec_start)
        elif est:
            k = min(est, key=lambda k: abs(est[k] - old))
            n = k if abs(est[k] - old) <= 15 else None
        if n is None:
            k = max(sections, key=lambda k: difflib.SequenceMatcher(None, norm(sections[k]["name"]), norm(name)).ratio())
            if difflib.SequenceMatcher(None, norm(sections[k]["name"]), norm(name)).ratio() >= 0.4:
                n = k
        if n is None or n not in sec_start:
            todo.append(f"Chapter '{l.strip()}' does not match a guide section - its time was left unchanged.")
            chap.append([i, old, name, old])
        else:
            chap.append([i, 0 if old == 0 else int(sec_start[n]), name, old])
    if not chap:  # no chapters written yet -> create them from the guide sections
        skip = re.compile(r"\b(CTA|PROMO|SUBSCRIBE|LIKE|TRANSITION|OUTRO)\b", re.I)
        for n in sorted(sec_start):
            if n == min(sec_start) or not skip.search(sections.get(n, {}).get("name", "")):
                chap.append([None, 0 if n == min(sec_start) else int(sec_start[n]), sections.get(n, {}).get("name", f"Part {n}").title(), None])
        ok.append("Chapters were created from the guide sections (none were in Description.txt).")
    chap.sort(key=lambda c: c[1])
    if chap and chap[0][1] != 0:
        chap[0][1] = 0
        ok.append("First chapter set to 0:00 (YouTube requires it).")
    kept, last = [], None
    for c in chap:
        if last is not None and c[1] - last[1] < 10:
            todo.append(f"Removed chapter '{c[2]}' - it starts less than 10 s after '{last[2]}' (YouTube would reject all chapters).")
            if c[0] is not None:
                lines[c[0]] = None
            continue
        if end_s - c[1] < 10:
            todo.append(f"Removed chapter '{c[2]}' - less than 10 s before the end.")
            if c[0] is not None:
                lines[c[0]] = None
            continue
        kept.append(c); last = c
    if len(kept) < 3:
        todo.append("YouTube needs at least 3 chapters (0:00 + 2 more) to show them.")
    moved = [f"   {yt_time(c[3])} -> {yt_time(c[1])}  {c[2]}" for c in kept if c[3] is not None and yt_time(c[3]) != yt_time(c[1])]
    if moved:
        ok.append("Chapter times corrected to match the finished edit:\n" + "\n".join(moved))
    elif any(c[3] is not None for c in kept):
        ok.append("Chapter times already match the edit.")
    for c in kept:
        if c[0] is not None:
            lines[c[0]] = f"{yt_time(c[1])} {c[2]}"
    if kept and all(c[0] is None for c in kept):
        block = ["TIMESTAMPS"] + [f"{yt_time(c[1])} {c[2]}" for c in kept] + [""]
        at = next((i for i, l in enumerate(lines) if l and re.match(r"^\s*(SOURCES|#)", l, re.I)), len(lines))
        lines[at:at] = block
    lines = [l for l in lines if l is not None and not CREDIT_LINE.search(l) and not re.fullmatch(r"\s*MUSIC( CREDITS)?:?\s*", l, re.I)]
    if music:
        lines += ["", "MUSIC"] + music
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
    if re.search(r"[<>]", text):
        text = text.replace("<", "").replace(">", "")
        ok.append("Removed < and > characters (YouTube does not allow them in descriptions).")
    if len(text) > 5000:
        todo.append(f"Description is {len(text)} characters - YouTube's limit is 5000.")
    tags_in_desc = re.findall(r"(?<![\w&])#\w+", text)
    if len(tags_in_desc) > 15:
        todo.append(f"{len(tags_in_desc)} hashtags - keep 3-5 (YouTube ignores ALL hashtags past 60; only the first 3 show above the title).")
    for ph in re.findall(r"\[[^\]\n]{1,60}\]", text):
        todo.append(f"Replace the placeholder {ph} in the description.")
    first = text.split("\n", 1)[0]
    key = [w for w in norm(title or "") if w not in GENERIC_TAG_WORDS]
    if key and not any(w in norm(first[:150]) for w in key):
        todo.append(f"The first line (what shows in search) doesn't mention '{' '.join(key)}'. Consider adding it.")
    m = re.search(r"(?im)^.*check out.*$\n((?:^(?!\s*$).*$\n?)+)", text)
    if m:
        nolink = [l.strip() for l in m.group(1).splitlines() if l.strip() and "http" not in l and not l.strip().startswith("#")]
        if nolink:
            todo.append("Add the YouTube links after: " + "; ".join(nolink))

    # ---- tags + pinned comments
    tag_p = find_txt(content, "tag", "keyword")
    tags, pinned = [], []
    if tag_p:
        raw = open(tag_p, encoding="utf-8-sig").read()
        cand = [l for l in raw.splitlines() if l.count(",") >= 2]
        if cand:
            seen = set()
            for t in max(cand, key=len).split(","):
                t = t.strip().strip('"“”').strip()
                if t and t.lower() not in seen:
                    seen.add(t.lower()); tags.append(t)
        pm = re.search(r"(?is)pinned[^\n]*\n(.*)", raw)
        if pm:
            pinned = [l.strip().strip('"“”').strip() for l in pm.group(1).splitlines() if l.strip()]
    else:
        todo.append("No 'Tags and keyword.txt' in the content folder.")
    if title and tags and not any(norm(t) == norm(title) for t in tags):
        tags.insert(0, title.rstrip("?!. ").lower())
        ok.append(f"Added the title as the first tag: '{tags[0]}'.")
    corpus_txt = " ".join(b["text"] + " " + b["action"] for b in beats) + " " + " ".join(s["name"] for s in sections.values()) + " " + (title or "")
    corpus = set(norm(corpus_txt))
    stems = {w[:5] for w in corpus if len(w) >= 5}
    off = [t for t in tags if [w for w in norm(t) if w not in GENERIC_TAG_WORDS]
           and not any(w in corpus or (len(w) >= 5 and w[:5] in stems) for w in norm(t) if w not in GENERIC_TAG_WORDS)]
    if off:
        todo.append("Check these tags - their words are never said in the video. Keep them only if they really describe it "
                    "(misleading tags can hurt): " + ", ".join(off))
    fit, dropped = [], []
    for t in tags:
        (fit if tag_chars(fit + [t]) <= 500 else dropped).append(t)
    if dropped:
        ok.append(f"Tags trimmed to YouTube's 500-character limit. Left out (lowest priority): {', '.join(dropped)}")
    for p in pinned:
        for ph in re.findall(r"\[[^\]\n]{1,60}\]", p):
            todo.append(f"Pinned comment has a placeholder {ph}: \"{p[:60]}...\"")
    if title and len(title) > 100:
        todo.append(f"Title is {len(title)} characters - YouTube's limit is 100.")

    out = [f"YOUTUBE UPLOAD  -  made by AutoEditLongForm {time.strftime('%Y-%m-%d %H:%M')}",
           f"Built from: {os.path.basename(desc_p) if desc_p else '-'}, {os.path.basename(tag_p) if tag_p else '-'}, the guide and the finished edit ({yt_time(end_s)}).",
           "Your original files were not changed.", "",
           "==================== TITLE ====================", title or "(add a title line to the guide)", "",
           "==================== DESCRIPTION (copy everything until the next ==== line) ====================", text.rstrip(), "",
           f"==================== TAGS ({tag_chars(fit)}/500 characters, {len(fit)} tags) ====================", ", ".join(fit), ""]
    if pinned:
        out += ["==================== PINNED COMMENT (pick one) ===================="] + [f"{i}) {p}" for i, p in enumerate(pinned, 1)] + [""]
    out += ["==================== CHECKS ===================="] + [f"[done] {x}" for x in ok] + [f"[TO DO] {x}" for x in todo]
    if not todo:
        out.append("[done] Nothing left to fix.")
    dst = os.path.join(out_dir or content, "YOUTUBE UPLOAD.txt")
    open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
    log(f"\nYouTube upload text: {dst}")
    for x in todo:
        warn("Upload: " + x.split("\n")[0])
    return dst


def generate_thumbnail_prompt_autoedit(guide_path, folder, title):
    """Generate thumbnail_prompt.md for YouTube thumbnail creation."""
    
    with open(guide_path, 'r', encoding='utf-8') as f:
        guide_text = f.read()
    
    # Try to detect art style from guide
    art_style_keywords = {
        'hand-inked': 'hand-inked 2D storybook illustration',
        'storybook': 'hand-inked 2D storybook illustration',
        'flat': 'flat 2D vector illustration',
        'vector': 'flat 2D vector illustration',
        'stick': 'simple stick-figure style',
        'minimalist': 'minimalist flat design'
    }
    
    detected_style = "hand-inked 2D storybook illustration"  # Default
    guide_lower = guide_text.lower()
    for keyword, style in art_style_keywords.items():
        if keyword in guide_lower:
            detected_style = style
            break
    
    # Detect color palette from guide
    color_mentions = re.findall(r'#[0-9A-Fa-f]{6}', guide_text)
    has_custom_palette = len(color_mentions) > 0
    
    thumbnail_content = f"""# Thumbnail Generation Prompt
## Video: {title}

## Video Title
**"{title}"**

## Thumbnail Concept
[DESCRIBE YOUR THUMBNAIL CONCEPT HERE]
- Character/subject positioning (left third, center, right)
- Background/scene description
- Key visual elements that capture attention
- Emotional tone (dramatic, curious, shocking, etc.)

## Art Style Specifications
**Style:** {detected_style}

### Visual Details
- Painterly or vector approach (match your content style)
- Line work: thick outlines, cross-hatching, clean vectors
- Character design: simple or detailed
- Environment: richly detailed or minimalist
- Texture: watercolor washes, flat colors, gradients

### Color Palette
**Primary Colors:**
{chr(10).join(f'- Color name #{color}' for color in color_mentions[:5]) if has_custom_palette else '''- [Define your primary colors with hex codes]
- Example: Deep Blue #2B3350
- Example: Warm Ochre #C9A66B'''}

**Accent Colors:**
- [Define accent colors for highlights, text, emphasis]

## Composition Layout

### Text Overlay
**Primary Text:**
- "[MAIN HOOK TEXT]"
- Font: Bold, hand-drawn or impactful style
- Color: Bright yellow #FFD700 or contrasting color
- Outline: Thick black stroke (3-4px) for readability
- Position: Upper or center area, over less busy background
- Size: Large enough to read on mobile (40-50% of thumbnail height)

**Secondary Text (Optional):**
- "[Supporting text if needed]"
- Same style but 30% smaller

### Visual Elements
**Character/Subject Positioning:**
- Position: [Left third / Center / Right side]
- Close-up or full figure
- Expression and pose
- Key props or identifying features

**Background/Scene:**
- Setting description
- Depth and layers
- Supporting visual elements
- Atmospheric effects (lighting, mood)

## Mood & Atmosphere
- **Tone**: [Mysterious / Dramatic / Educational / Shocking / etc.]
- **Emotion**: [Curiosity / Fear / Wonder / Intrigue / etc.]
- **Era/Setting**: [Modern / Historical / Specific time period]
- **Energy**: [High energy / Contemplative / Intense / etc.]

## Technical Specifications
- **Dimensions**: 2752 x 1536 pixels (16:9 aspect ratio)
- **Resolution**: 72 DPI minimum
- **Format**: JPG, high quality
- **File Size**: Under 2MB for YouTube upload
- **Safe Zones**: Keep text/faces away from edges (10% margin)
- **Mobile Test**: Text must be legible at 320px width

## AI Image Generation Prompts

### Option 1: Midjourney/DALL-E
```
{detected_style}, [DESCRIBE YOUR SCENE]. Bold composition with [CHARACTER/SUBJECT] in [POSITION], [BACKGROUND DESCRIPTION]. Vibrant colors, dramatic lighting, cinematic framing. Large bold text "[YOUR TEXT]" with thick black outline. YouTube thumbnail style, eye-catching, high contrast, 16:9 aspect ratio --ar 16:9 --style raw
```

### Option 2: Stable Diffusion
```
{detected_style} :: [YOUR SCENE DESCRIPTION] :: [CHARACTER DETAILS] :: [BACKGROUND DETAILS] :: bold yellow text with black outline :: vibrant color palette :: dramatic lighting :: cinematic composition :: youtube thumbnail :: high contrast :: 16:9 aspect ratio --ar 16:9 --s 250
```

### Option 3: Detailed Prompt
```
Create a thumbnail in {detected_style} style. [DETAILED SCENE]. Character: [DESCRIPTION]. Background: [DESCRIPTION]. Colors: [YOUR PALETTE]. Text overlay: "[YOUR TEXT]" in bold yellow with thick black outline, positioned [LOCATION]. Lighting: [DESCRIPTION]. Mood: [MOOD]. YouTube thumbnail optimized, eye-catching composition, 2752x1536px.
```

## Production Checklist
- [ ] Art style matches content videos
- [ ] Text is large and readable on mobile
- [ ] High contrast between text and background
- [ ] Character/subject has clear facial expression or recognizable feature
- [ ] Colors are vibrant and eye-catching
- [ ] Composition follows rule of thirds
- [ ] All important elements in safe zones (away from edges)
- [ ] Tested at thumbnail size (check 320px width preview)
- [ ] File size under 2MB
- [ ] Resolution 2752x1536 or higher

## Alternative Concepts
If the main concept doesn't work, try:

### Concept 2: [Alternative approach]
- Different composition or angle
- Different text hook
- Different color emphasis

### Concept 3: [Another alternative]
- Character vs. scene focus shift
- Close-up vs. wide shot
- Different emotional tone

## Notes
- Generate at 2x resolution (5504x3072) then downscale for crisp text
- Test multiple text positions before finalizing
- Ensure thumbnail stands out in YouTube's grid of suggestions
- A/B test different hooks if possible
- Keep consistent with your channel's brand style

---

**Remember:** Thumbnails drive 80%+ of clicks. Invest time in getting this right!
"""
    
    thumbnail_path = os.path.join(folder, "thumbnail_prompt.md")
    with open(thumbnail_path, 'w', encoding='utf-8') as f:
        f.write(thumbnail_content)
    
    return thumbnail_path


def main():
    ap = argparse.ArgumentParser(description="Build a CapCut timeline from a content folder.")
    ap.add_argument("content", nargs="?", help="content folder (Pictures, Voice, guide .md)")
    ap.add_argument("--project", help="CapCut project name to fill (create an empty project in CapCut first)")
    ap.add_argument("--project-dir", help="explicit CapCut project folder (advanced/testing)")
    ap.add_argument("--dry-run", action="store_true", help="build + check, but do not touch CapCut")
    ap.add_argument("--retranscribe", action="store_true", help="ignore saved transcripts")
    ap.add_argument("--reset-texts", action="store_true", help="re-create texts.json from the guide")
    ap.add_argument("--upload-only", action="store_true",
                    help="only (re)make 'YOUTUBE UPLOAD.txt' from the existing CapCut edit (reads the project, changes nothing)")
    ap.add_argument("--idea", help="video idea/topic (auto-generates missing content)")
    ap.add_argument("--length", type=int, default=8, help="target video length in minutes (default: 8)")
    args = ap.parse_args()

    content = args.content or input("Drag the content folder here and press Enter: ").strip().strip('"')
    content = os.path.abspath(content)
    
    # Check if content generation is needed
    if args.idea or not os.path.isdir(content):
        log("=" * 80)
        log("Checking content availability...")
        log("=" * 80)
        
        # Call autogenerate to check/create missing content
        import subprocess
        autogen_path = os.path.join(HERE, "autogenerate.py")
        cmd = [sys.executable, autogen_path, content]
        if args.idea:
            cmd += ["--idea", args.idea, "--length", str(args.length)]
        
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            sys.exit(result.returncode)
        
        # Check if content is now ready
        try:
            C_check = find_content(content)
        except SystemExit:
            log("\nContent not ready yet. Complete the steps above, then run AutoEdit again.")
            return
        
        log("\n" + "=" * 80)
        log("Content ready! Proceeding with auto-edit...")
        log("=" * 80 + "\n")
    cfg = jload(os.path.join(HERE, "settings.json"))
    work = os.path.join(content, "_autoedit")
    os.makedirs(work, exist_ok=True)
    if os.path.exists(os.path.join(work, "settings.json")):
        cfg = deep_merge(cfg, jload(os.path.join(work, "settings.json")))
        log("Using per-video settings from _autoedit\\settings.json")

    if args.dry_run:
        proj = args.project_dir
    elif args.upload_only:
        proj = args.project_dir or pick_project(args.project)
    else:
        if capcut_running():
            sys.exit("CapCut is open. Close CapCut completely, then run AutoEdit again.")
        proj = args.project_dir or pick_project(args.project)
    base_path = os.path.join(proj, "draft_content.json") if proj else None
    if base_path and not os.path.exists(base_path):
        sys.exit(f"No draft_content.json in {proj}")
    try:
        base = jload(base_path) if base_path else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        sys.exit("This CapCut project file is encrypted/unreadable. AutoEdit needs CapCut 9.x drafts (plain JSON).")
    if base is None:
        base = jload(os.path.join(HERE, "templates", "empty_draft.json")) if os.path.exists(
            os.path.join(HERE, "templates", "empty_draft.json")) else sys.exit("--dry-run needs --project-dir or templates/empty_draft.json")

    T = jload(os.path.join(HERE, "templates", "capcut_templates.json"))
    C = find_content(content)
    title, beats, sections = parse_guide(C["guide"])
    log(f"Guide: {os.path.basename(C['guide'])}  |  {len(beats)} beats  |  {len(C['images'])} images  |  {len(C['voice'])} voice files")
    if title:
        log(f"Title: {title}")

    # ---------------- voice + alignment
    vdur = [media_dur_us(p) for p in C["voice"]]
    words_per_file = transcribe(C["voice"], work, cfg["whisper_model"], args.retranscribe)
    words, tok_time, vo_end = align(beats, words_per_file, [d / US for d in vdur], cfg["timing"]["lead_in_s"])
    vo_end = sum(vdur) / US
    END = vo_end + cfg["timing"]["tail_s"]
    TB = {b["n"]: b for b in beats}
    if args.upload_only:
        if not base.get("tracks"):
            sys.exit("That CapCut project is empty - run AutoEdit first (without --upload-only).")
        make_upload(content, title, beats, sections, base)
        return

    lib_cache_p = os.path.join(YTA, "Library", "_loudness_cache.json")
    os.makedirs(os.path.dirname(lib_cache_p), exist_ok=True)
    lcache = jload(lib_cache_p) if os.path.exists(lib_cache_p) else {}
    
    log("\nAnalyzing voice audio levels...")
    vo_stats = [analyse_audio(p, lcache) for p in C["voice"]]
    vo_active = sum(s["active_db"] * d for s, d in zip(vo_stats, vdur)) / sum(vdur)
    vo_peak = max(s["sample_peak_db"] for s in vo_stats)
    
    vo_gain_db = 0.0
    if cfg["voice"]["normalize"]:
        # Calculate gain to reach target loudness without clipping
        target_gain = cfg["voice"]["target_db"] - vo_active
        peak_limit = cfg["voice"]["max_peak_db"] - vo_peak
        vo_gain_db = min(target_gain, peak_limit)
        vo_gain_db = max(-6.0, min(12.0, vo_gain_db))  # Safety limits: -6 to +12 dB
        
        log(f"  Current voice loudness: {vo_active:.1f} dB")
        log(f"  Current peak level: {vo_peak:.1f} dB")
        log(f"  Target loudness: {cfg['voice']['target_db']:.1f} dB")
        log(f"  Applying gain: {vo_gain_db:+.1f} dB")
        log(f"  Final loudness: {vo_active + vo_gain_db:.1f} dB")
        log(f"  Final peak: {vo_peak + vo_gain_db:.1f} dB")
    else:
        log("  Voice normalization is disabled in settings.json")
    
    vo_level = vo_active + vo_gain_db
    jsave(lib_cache_p, lcache)  # Save cache

    # ---------------- project pool (media panel)
    meta_p = os.path.join(proj, "draft_meta_info.json") if proj else None
    meta = jload(meta_p) if meta_p and os.path.exists(meta_p) else {"draft_materials": [{"type": 0, "value": []}]}
    g0 = next((g for g in meta["draft_materials"] if g["type"] == 0), None)
    if g0 is None:
        g0 = {"type": 0, "value": []}; meta["draft_materials"].append(g0)
    pool = {os.path.normcase(x["file_Path"]): x for x in g0["value"] if x.get("file_Path")}
    added = []

    def pool_id(path, kind, dur_us=0, w=0, h=0):
        k = os.path.normcase(path)
        if k not in pool:
            now = int(time.time())
            e = {"ai_group_type": "", "create_time": now, "duration": dur_us if kind == "music" else 5000000, "enter_from": 0,
                 "extra_info": os.path.basename(path), "file_Path": path, "height": h, "id": str(uuid.uuid4()),
                 "import_time": now, "import_time_ms": int(time.time() * 1e6), "item_source": 1, "material_color_tag": "",
                 "md5": "", "metetype": kind,
                 "roughcut_time_range": {"duration": dur_us, "start": 0} if kind == "music" else {"duration": -1, "start": -1},
                 "sub_time_range": {"duration": -1, "start": -1}, "type": 0, "width": w}
            pool[k] = e; g0["value"].append(e); added.append(e)
        return pool[k]["id"]

    B = Builder(base, T)

    # ---------------- pictures + zoom
    from PIL import Image
    shots = []
    for b in beats:
        if b["n"] in C["images"]:
            shots.append((b["cut"], b["n"]))
        elif shots:
            warn(f"No image for beat {b['n']} - the previous image stays on screen.")
        else:
            nxt = min(C["images"])
            warn(f"No image for beat {b['n']} - using image {nxt}.")
            shots.append((0.0, nxt))
    extra_imgs = sorted(set(C["images"]) - set(TB))
    if extra_imgs:
        warn(f"Images without a beat in the guide (not used): {extra_imgs[:10]}")
    vt = B.track("video")
    zc = cfg["zoom"]
    
    # Smart zoom analysis
    zoom_analysis = []
    for i, (st, num) in enumerate(shots):
        b = TB[num]
        action_text = b["action"].lower() + " " + b["text"].lower()
        
        # Detect if image should be static or slow zoom
        zoom_mode = "NORMAL"
        reason = ""
        
        if zc.get("smart_detection", False):
            # Check for static keywords
            static_kw = zc.get("static_keywords", [])
            for kw in static_kw:
                if kw in action_text:
                    zoom_mode = "STATIC"
                    reason = f"keyword: {kw}"
                    break
            
            # Check for slow zoom keywords if not static
            if zoom_mode == "NORMAL":
                slow_kw = zc.get("slow_zoom_keywords", [])
                for kw in slow_kw:
                    if kw in action_text:
                        zoom_mode = "SLOW"
                        reason = f"keyword: {kw}"
                        break
        
        zoom_analysis.append((num, zoom_mode, reason))
        b["_zoom_mode"] = zoom_mode
    
    for i, (st, num) in enumerate(shots):
        path = C["images"][num]
        b = TB[num]
        s_us = fr(st)
        # Use beat's explicit end time if available, otherwise use next shot's start or END
        if i + 1 < len(shots):
            e_us = fr(shots[i + 1][0])
        else:
            # Last image: use beat's end time if specified, otherwise use END
            e_us = fr(b["end"])
        dur = e_us - s_us
        if dur / US > cfg["timing"]["warn_shot_longer_than_s"]:
            warn(f"Image {num} is on screen {dur / US:.1f}s (long). Consider an extra image for that beat.")
        with Image.open(path) as im:
            w, h = im.size
        pool_id(path, "photo", w=w, h=h)
        cover = max(1.0, 1080 / (1920 * h / w), 1920 / (1080 * w / h)) if zc["fill_frame"] else 1.0
        
        # Apply zoom based on mode
        zoom_mode = b.get("_zoom_mode", "NORMAL")
        
        if zoom_mode == "STATIC":
            # No zoom - keep at cover scale
            a = bz = cover
        elif zoom_mode == "SLOW":
            # Reduced zoom range
            slow_factor = zc.get("slow_zoom_factor", 0.6)
            zoom_range = (zc["max"] - zc["min"]) * slow_factor
            a, bz = zc["min"] * cover, (zc["min"] + zoom_range) * cover
            if zc["alternate"] and i % 2:
                a, bz = bz, a
        else:
            # Normal zoom
            a, bz = zc["min"] * cover, zc["max"] * cover
            if zc["alternate"] and i % 2:
                a, bz = bz, a
        
        end_t = dur - int(FRAME)
        if zoom_mode == "STATIC" or abs(a - bz) < 0.01:
            pts = [(0, a), (end_t, a)]  # Static
        elif zc["easing"] == "ease":
            pts = [(int(end_t * u), a + (bz - a) * (1 - math.cos(math.pi * u)) / 2) for u in (0, 0.25, 0.5, 0.75, 1.0)]
        else:
            pts = [(0, a), (end_t, bz)]
        
        anim = None
        if i == 0 and "Fade In" in T["animations"]:
            anim = dict(copy.deepcopy(T["animations"]["Fade In"]), start=0, duration=600000)
        if i == len(shots) - 1 and "Fade Out" in T["animations"]:
            fo = min(1500000, dur // 2)
            anim = dict(copy.deepcopy(T["animations"]["Fade Out"]), start=dur - fo, duration=fo)
        B.photo(vt, path, w, h, s_us, dur, pts, anim)

    # ---------------- texts
    tcfg = cfg["text"]
    texts_p = os.path.join(work, "texts.json")
    if tcfg["enabled"]:
        if args.reset_texts or not os.path.exists(texts_p):
            jsave(texts_p, {"_help": "One entry per on-screen label. beat = beat number from the guide; at = the word(s) "
                                     "from that beat's script when the label pops in; text = what shows ('|' adds a smaller "
                                     "second line, e.g. a job title); pos = lower | upper | right | left | center. Delete an "
                                     "entry to remove a label. Run AutoEdit again to apply.",
                            "labels": auto_texts(title, beats, cfg)}, pretty=True)
            log("Created _autoedit\\texts.json (edit it to change labels).")
        labels = jload(texts_p)["labels"]
    else:
        labels = []
    font = tcfg["font"] if os.path.exists(tcfg["font"]) else lib_path(tcfg["font_fallback"])
    POS = {"lower": (0.0, tcfg["lower_y"]), "upper": (0.0, -tcfg["lower_y"]), "right": (0.56, 0.12),
           "left": (-0.56, 0.12), "center": (0.0, 0.0)}
    events = []
    for L in labels:
        b = TB.get(L["beat"])
        if not b:
            warn(f"texts.json: beat {L['beat']} does not exist."); continue
        t0 = anchor_time(b, L.get("at"), tok_time, words) - 0.05
        pos = L.get("pos", "lower")
        x, y = (L["x"], L["y"]) if "x" in L else POS.get(pos, POS["lower"])
        side = pos in ("right", "left")
        if b["end"] - t0 >= 1.0:
            t1 = b["end"]
        else:
            t1 = t0 + tcfg["min_on_screen_s"]
        t1 = min(t1, t0 + tcfg["max_on_screen_s"], END - 0.2)
        if L.get("until_end") or b is beats[-1]:
            t1 = END - 0.3
        main, _, sub = L["text"].partition("|")
        width, lines = (14, 3) if side else (34, 3) if pos == "center" else (26, 2)
        main = wrap(main, width, lines)
        events.append({"t0": t0, "t1": t1, "main": main, "sub": sub.strip(), "x": x, "y": y,
                       "scale": L.get("scale", tcfg["title_scale"] if side else tcfg["label_scale"]), "slot": (x, y)})
    events.sort(key=lambda e: e["t0"])
    kept, last_by_slot = [], {}
    for e in events:
        prev = last_by_slot.get(e["slot"])
        if prev and e["t0"] - prev["t0"] < tcfg["min_gap_between_labels_s"]:
            warn(f"Skipped label '{e['main']}' (too close to '{prev['main']}').")
            continue
        if prev and prev["t1"] > e["t0"] - 0.1:
            prev["t1"] = e["t0"] - 0.1
        last_by_slot[e["slot"]] = e
        kept.append(e)
    text_tracks, slot_track = [], {}
    for e in kept:
        tr = slot_track.get(e["slot"])
        if tr is None or tr["_end"] > e["t0"]:
            tr = next((t for t in text_tracks if t["_end"] <= e["t0"] and t is not slot_track.get(e["slot"])), None) or B.track("text")
            if tr not in text_tracks:
                tr["_end"] = 0; text_tracks.append(tr)
            slot_track[e["slot"]] = tr
        sizes = [15] * len(e["main"].split("\n")) + ([10] if e["sub"] else [])
        full = e["main"] + ("\n" + e["sub"] if e["sub"] else "")
        while True:
            l, r, top, bot = text_box(full, sizes, e["scale"], e["x"], e["y"], font)
            if (l >= 40 and r <= 1880 and top >= 30 and bot <= 1050) or e["scale"] < 0.3:
                break
            e["scale"] *= 0.92
        s_us, e_us = fr(e["t0"]), fr(e["t1"])
        if e_us - s_us < 2 * FRAME * 7:
            continue
        B.text(tr, text_tracks.index(tr), {"main": e["main"], "sub": e["sub"]}, s_us, e_us - s_us, e["x"], e["y"], e["scale"], tcfg, font)
        tr["_end"] = e["t1"]
        e["placed"] = True

    # ---------------- voice
    vo = B.track("audio")
    off = 0
    for p, d in zip(C["voice"], vdur):
        B.audio(vo, p, pool_id(p, "music", d), d, off, 0, d, round(10 ** (vo_gain_db / 20), 4))
        off += d

    # ---------------- music
    mcfg, cues, credits, music_log = cfg["music"], [], [], []
    if mcfg["enabled"]:
        mroot = lib_path(mcfg["folder"])
        secs = []
        for b in beats:
            if not secs or secs[-1]["id"] != b["sec"]:
                secs.append({"id": b["sec"], "beats": [], "start": b["cut"]})
            secs[-1]["beats"].append(b)
        for i, s in enumerate(secs):
            s["end"] = secs[i + 1]["start"] if i + 1 < len(secs) else END
            s["mood"] = mood_of(s["beats"], cfg)
        for s in secs:
            name = f"{s['id'][0]}:{s['mood']}"
            if cues and cues[-1]["mood"] == s["mood"]:
                cues[-1]["end"] = s["end"]; cues[-1]["names"].append(name)
            else:
                cues.append({"mood": s["mood"], "start": s["start"], "end": s["end"], "names": [name]})
        merged = []  # fold cues shorter than min_cue_s into a neighbour (the longer, earlier cue keeps its mood)
        for c in cues:
            if merged and c["end"] - c["start"] < mcfg["min_cue_s"]:
                merged[-1]["end"] = c["end"]; merged[-1]["names"] += c["names"]
            elif merged and merged[-1]["end"] - merged[-1]["start"] < mcfg["min_cue_s"]:
                c["start"] = merged[-1]["start"]; c["names"] = merged[-1]["names"] + c["names"]; merged[-1] = c
            else:
                merged.append(c)
        cues = []
        for c in merged:
            if cues and cues[-1]["mood"] == c["mood"]:
                cues[-1]["end"] = c["end"]; cues[-1]["names"] += c["names"]
            else:
                cues.append(c)
        rng = random.Random(os.path.basename(content))
        lists, used = {}, set()

        def next_track(mood, need_s):
            """Unused track of this mood, preferring one long enough to cover the whole cue (no 3-second leftovers)."""
            for m in [mood, mcfg["default_mood"]] + sorted(os.listdir(mroot)):
                if m not in lists:
                    fs = sorted(glob.glob(os.path.join(mroot, m, "*.mp3")))
                    rng.shuffle(fs); lists[m] = fs
                fresh = [f for f in lists[m] if f not in used] or lists[m]
                if fresh:
                    long_enough = [f for f in fresh if media_dur_us(f) / US >= need_s + 0.5]
                    f = long_enough[0] if long_enough else max(fresh, key=media_dur_us)
                    used.add(f)
                    return f.replace("\\", "/")
            sys.exit(f"No music found in {mroot}")

        mtracks = [B.track("audio"), B.track("audio")]
        XF = mcfg["crossfade_s"]
        k = 0
        for ci, c in enumerate(cues):
            a = 0.0 if ci == 0 else c["start"] - XF / 2
            end_all = END if ci == len(cues) - 1 else c["end"] + XF / 2
            while a < end_all - 0.5:
                f = next_track(c["mood"], end_all - a)
                full = media_dur_us(f)
                b_ = min(end_all, a + full / US - 0.1)
                st = analyse_audio(f, lcache)
                gain = 10 ** ((vo_level - mcfg["under_voice_db"] - st["active_db"]) / 20)
                last = ci == len(cues) - 1 and b_ >= end_all - 1e-6
                fin = int(0.8 * US) if k == 0 else int(XF * US)
                fout = int(mcfg["end_fade_s"] * US) if last else int(XF * US)
                s_us, e_us = fr(a), fr(b_)
                B.audio(mtracks[k % 2], f, pool_id(f, "music", full), full, s_us, 0, e_us - s_us, round(gain, 4), fin, fout)
                credits.append(os.path.splitext(os.path.basename(f))[0])
                music_log.append(f"{a:8.1f}-{b_:7.1f}s  {c['mood']:10s} {os.path.basename(f):26s} sections: {', '.join(c['names'])}")
                log("  music " + music_log[-1])
                k += 1
                if b_ >= end_all - 1e-6:
                    break
                a = b_ - XF

    # ---------------- sound effects
    scfg, sfx = cfg["sfx"], []
    if scfg["enabled"]:
        sroot = lib_path(scfg["folder"])
        rng = random.Random("sfx" + os.path.basename(content))

        def sfx_file(spec):
            p = os.path.join(sroot, spec)
            if os.path.isfile(p):
                return p.replace("\\", "/"), spec.split("/")[0].split("\\")[0]
            fs = sorted(glob.glob(os.path.join(sroot, spec, "*.mp3")) + glob.glob(os.path.join(sroot, spec, "*.wav")))
            if not fs:
                warn(f"No sound found for '{spec}' in {sroot}"); return None, None
            return rng.choice(fs).replace("\\", "/"), spec

        def add(t_hit, spec, extra_db=0.0):
            f, cat = sfx_file(spec)
            if not f:
                return
            st = analyse_audio(f, lcache)
            lvl = scfg["levels_db"].get(cat, -6) + extra_db
            sfx.append((t_hit - st["peak_t"], f, 10 ** ((vo_level + lvl - st["peak_db"]) / 20)))

        sec_first = []
        for i, b in enumerate(beats):
            if i and b["sec"] != beats[i - 1]["sec"]:
                sec_first.append(b)
        riser_words = [w.upper() for w in scfg["riser_before_sections_named"]]
        for b in sec_first:
            if any(w in b["sec"][1].upper() for w in riser_words):
                add(b["cut"], "Riser")
            elif scfg["whoosh_on_section_change"]:
                add(b["cut"], "Whoosh")
        if scfg["pop_on_text"]:
            for e in kept:
                if e.get("placed"):
                    add(e["t0"] + 0.03, "Pop")
        if scfg["ding_on_subscribe_and_like"]:
            for b in beats:
                low = b["text"].lower()
                for w in ("subscribe", "like"):
                    if w in b["tokens"] and (w == "subscribe" or "like button" in low):
                        add(anchor_time(b, w, tok_time, words) + 0.25, "Ding")
                        break
        last_at = {}
        for pat, spec in scfg["image_keywords"].items():
            if pat.startswith("_"):
                continue
            for b in beats:
                if re.search(pat, b["action"], re.I) and b["n"] in C["images"]:
                    if b["cut"] - last_at.get(spec, -1e9) >= scfg["same_sound_min_gap_s"]:
                        add(b["cut"] + 0.25, spec); last_at[spec] = b["cut"]
        xs_p = os.path.join(work, "extra_sfx.json")
        if not os.path.exists(xs_p):
            jsave(xs_p, {"_help": "Add your own sound effects: beat = beat number, at = word in that beat's script, "
                                  "sound = a Library\\SFX category (Whoosh, Pop, Ding, Riser, Camera, Impact, Meme) or a file "
                                  "like 'Meme/vine-boom.mp3', volume_db = optional +/- adjustment. Example: "
                                  "{\"beat\": 27, \"at\": \"lice\", \"sound\": \"Impact\"}",
                         "sounds": []}, pretty=True)
        for x in jload(xs_p).get("sounds", []):
            b = TB.get(x.get("beat"))
            if b:
                add(anchor_time(b, x.get("at"), tok_time, words), x["sound"], x.get("volume_db", 0.0))
        if C["extra_sfx_dir"]:
            log(f"  (per-video SFX folder found: {C['extra_sfx_dir']} - use them via extra_sfx.json with a full path)")
        sfx.sort()
        sfx_tracks = []
        for st, f, gain in sfx:
            full = media_dur_us(f)
            s_us = max(0, fr(st))
            dur = min(full, fr(END) - s_us)
            if dur <= 0:
                continue
            tr = next((t for t in sfx_tracks if t["_end"] <= s_us), None)
            if tr is None:
                tr = B.track("audio"); tr["_end"] = 0; sfx_tracks.append(tr)
            B.audio(tr, f, pool_id(f, "music", full), full, s_us, 0, dur, round(min(gain, 4.0), 4))
            tr["_end"] = s_us + dur

    # ---------------- finalise
    for t in B.tracks:
        t.pop("_end", None)
        t["segments"].sort(key=lambda s: s["target_timerange"]["start"])
    B.tracks = [t for t in B.tracks if t["segments"]]
    for i, t in enumerate(B.tracks):
        if t["type"] == "audio":
            for s in t["segments"]:
                s["track_render_index"] = i
    d = B.d
    d["tracks"] = B.tracks
    d["duration"] = max(s["target_timerange"]["start"] + s["target_timerange"]["duration"] for t in d["tracks"] for s in t["segments"])
    d["canvas_config"] = {"ratio": "original", "width": 1920, "height": 1080, "background": None}
    jsave(lib_cache_p, lcache, pretty=True)

    errs = validate(d)
    if errs:
        for e in errs[:30]:
            log("  ERROR", e)
        sys.exit(f"{len(errs)} problems found - nothing was written to CapCut.")

    report = [f"AutoEdit report  {time.strftime('%Y-%m-%d %H:%M')}", f"Content: {content}", f"CapCut project: {proj or '(dry run)'}",
              f"Length: {d['duration'] / US / 60:.0f}:{d['duration'] / US % 60:04.1f}  |  images {len(shots)}  |  labels {sum(1 for e in kept if e.get('placed'))}"
              f"  |  sound effects {len(sfx)}  |  music tracks {len(credits)}",
              f"Voice level {vo_active:.1f} dB -> {vo_level:.1f} dB (gain {vo_gain_db:+.1f} dB)", ""] + \
             (["ZOOM ANALYSIS (smart detection enabled):" if zc.get("smart_detection") else ""] if zc.get("smart_detection") else []) + \
             ([f" - Beat {num}: {mode}" + (f" ({reason})" if reason else "") for num, mode, reason in zoom_analysis if mode != "NORMAL"] if zc.get("smart_detection") else []) + \
             ["", "WARNINGS:"] + [" - " + w for w in WARN] + ["", "MUSIC (start-end, mood, track, guide sections number:mood):"] + music_log + \
             ["", "BEATS (start  length  beat  script):"] + \
             [f"{b['cut']:8.2f} {b['end'] - b['cut']:5.1f}s  {b['n']:4d}  {b['text'][:70]}" for b in beats] + \
             ["", "LABELS:"] + [f"{e['t0']:8.2f}  {e['main']!r} {e['sub']!r}" for e in kept if e.get("placed")]
    open(os.path.join(work, "report.txt"), "w", encoding="utf-8").write("\n".join(report))
    if credits:
        reg = load_credits()
        lines = ["Music (already included in YOUTUBE UPLOAD.txt):", ""]
        for c in dict.fromkeys(credits):
            lines += (credit_lines(c, reg) or [f"{c} - credit text missing, add it to Library\\Music\\credits.json"]) + [""]
        open(os.path.join(work, "MUSIC_CREDITS.txt"), "w", encoding="utf-8").write("\n".join(lines))

    out = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    if args.dry_run:
        ddir = os.path.join(work, "dry_run")
        os.makedirs(ddir, exist_ok=True)
        open(os.path.join(ddir, "draft_content.json"), "w", encoding="utf-8").write(out)
        log(f"\nDRY RUN OK - nothing written to CapCut. Preview file: {ddir}")
    else:
        bdir = os.path.join(work, "backups", time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(bdir, exist_ok=True)
        for f in ("draft_content.json", "draft_meta_info.json", "draft_virtual_store.json"):
            if os.path.exists(os.path.join(proj, f)):
                shutil.copy2(os.path.join(proj, f), bdir)
        for old in sorted(glob.glob(os.path.join(work, "backups", "*")))[:-5]:
            shutil.rmtree(old, ignore_errors=True)
        targets = [os.path.join(proj, "draft_content.json"), os.path.join(proj, "draft_content.json.bak"),
                   os.path.join(proj, "template-2.tmp")]
        tl = timeline_dir(proj)
        if tl:
            targets += [os.path.join(tl, n) for n in ("draft_content.json", "draft_content.json.bak", "template-2.tmp")]
        for p in targets:
            if os.path.exists(p) or p.endswith("draft_content.json"):
                open(p, "w", encoding="utf-8").write(out)
        now_us = int(time.time() * 1e6)
        if meta_p:
            meta.update(tm_duration=d["duration"], tm_draft_modified=now_us, draft_fold_path=proj.replace("\\", "/"))
            jsave(meta_p, meta)
        vs_p = os.path.join(proj, "draft_virtual_store.json")
        if os.path.exists(vs_p) and added:
            vs = jload(vs_p)
            v1 = next((g for g in vs.get("draft_virtual_store", []) if g["type"] == 1), None)
            if v1 is not None:
                have = {x["child_id"] for x in v1["value"]}
                v1["value"] += [{"child_id": e["id"], "parent_id": ""} for e in added if e["id"] not in have]
                jsave(vs_p, vs)
        rp = os.path.join(CAPCUT_ROOT, "root_meta_info.json")
        if os.path.exists(rp) and meta.get("draft_id"):
            root = jload(rp)
            for x in root.get("all_draft_store", []):
                if x.get("draft_id") == meta["draft_id"]:
                    x["tm_duration"] = d["duration"]; x["tm_draft_modified"] = now_us
            jsave(rp, root)
        log(f"\nDONE - open CapCut and open project '{os.path.basename(proj)}'.")
    make_upload(content, title, beats, sections, d, os.path.join(work, "dry_run") if args.dry_run else None)
    open(os.path.join(work, "report.txt"), "a", encoding="utf-8").write(
        "\n\nUPLOAD CHECKS:\n" + "\n".join(" - " + w for w in WARN if w.startswith("Upload:")))
    log(f"Report: {os.path.join(work, 'report.txt')}" + (f"\nMusic credits: {os.path.join(work, 'MUSIC_CREDITS.txt')}" if credits else ""))
    if WARN:
        log(f"{len(WARN)} warning(s) - see the report.")
    
    # Generate thumbnail prompt if it doesn't exist
    thumbnail_path = os.path.join(content, "thumbnail_prompt.md")
    if not os.path.exists(thumbnail_path):
        log("\n🎨 Generating thumbnail prompt...")
        try:
            generate_thumbnail_prompt_autoedit(C["guide"], content, title or "Your Video")
            log(f"✓ Created {os.path.basename(thumbnail_path)}")
        except Exception as e:
            log(f"⚠️  Could not generate thumbnail prompt: {e}")


if __name__ == "__main__":
    main()
