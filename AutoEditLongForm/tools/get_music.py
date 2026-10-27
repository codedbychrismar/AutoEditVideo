"""Download the curated informative (non-comedy) Kevin MacLeod music library, and write
Library\\Music\\credits.json (exact credit text per track, used by AutoEdit for the YouTube description)
and Library\\Music\\CREDITS.txt. Run again any time; existing files are skipped. Add titles to PICKS to grow the library.
Credits you add by hand to credits.json for other music are kept."""
import json, os, urllib.parse, urllib.request

MUSIC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Library", "Music")
LIB = os.path.join(MUSIC, "Informative")
CATALOG = "https://incompetech.com/music/royalty-free/pieces.json"
BASE = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/"

PICKS = {
    "Curious": ["Groove Grove", "Clean Soul", "Andreas Theme", "Almost New", "Unwritten Return"],
    "Calm": ["Inspired", "Light Thought var 1", "Dreamer", "Deliberate Thought", "Easy Lemon"],
    "Upbeat": ["Wallpaper", "Carefree", "On My Way", "Backbay Lounge", "Sunshine"],
    "Serious": ["Danse Morialta", "Promises to Keep", "The Parting", "Calmant", "Dreams Become Real"],
    "Mystery": ["Hard Boiled", "Spy Glass", "Kool Kats", "Sunday Dub"],
    "Historical": ["Teller of the Tales", "Tabuk", "Maple Leaf Rag", "Canon in D Major"],
}
# Kevin MacLeod tracks kept in the old YT Automation\Sounds\Music folder (used by older edits) - credit only, no download
LEGACY = ["Investigations", "Thinking Music", "Hidden Agenda", "Sneaky Snitch"]


def credit(title):
    return [f"{title} Kevin MacLeod (incompetech.com)", "Licensed under Creative Commons: By Attribution 4.0 License",
            "http://creativecommons.org/licenses/by/4.0/"]


def main():
    pieces = {p["title"]: p for p in json.load(urllib.request.urlopen(CATALOG, timeout=60))}
    cpath = os.path.join(MUSIC, "credits.json")
    reg = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}
    reg["_help"] = "Track title (= mp3 file name without .mp3) -> exact credit lines for the YouTube description. Add your own music here."
    for mood, titles in PICKS.items():
        os.makedirs(os.path.join(LIB, mood), exist_ok=True)
        for t in titles:
            p = pieces.get(t)
            if not p:
                print("not in catalog:", t); continue
            dst = os.path.join(LIB, mood, t + ".mp3")  # file name = exact title (used for the credit line)
            if not os.path.exists(dst):
                urllib.request.urlretrieve(BASE + urllib.parse.quote(p["filename"]), dst)
            print(f"{mood:10s} {t:25s} {p['length']}  [{p['feel']}]")
            reg[t] = credit(t)
    for t in LEGACY:
        reg.setdefault(t, credit(t))
    json.dump(reg, open(cpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(MUSIC, "CREDITS.txt"), "w", encoding="utf-8").write(
        "All tracks in Informative\\ are by Kevin MacLeod (CC BY 4.0).\n"
        "AutoEdit puts the right credits for each video into <content>\\YOUTUBE UPLOAD.txt automatically.\n\n"
        + "\n\n".join("\n".join(v) for k, v in reg.items() if not k.startswith("_")) + "\n")


if __name__ == "__main__":
    main()
