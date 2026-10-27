"""One-time: extract CapCut 9.x JSON object templates from existing (CapCut-written) drafts into
templates/capcut_templates.json, so autoedit.py never depends on old projects staying on disk."""
import json, os

ROOT = os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "capcut_templates.json")

def load(p):
    return json.load(open(os.path.join(ROOT, p, "draft_content.json"), encoding="utf-8"))

def index(d):
    return {x["id"]: (k, x) for k, v in d["materials"].items() for x in v if isinstance(x, dict) and "id" in x}

def seg_pack(d, ttype, i):
    seg = next(t for t in d["tracks"] if t["type"] == ttype)["segments"][i]
    idx = index(d)
    return {"segment": seg, "material": idx[seg["material_id"]][1],
            "extras": [{"category": idx[r][0], "object": idx[r][1]} for r in seg["extra_material_refs"]]}

video = seg_pack(load("1013"), "video", 1)      # CapCut 9.6 photo segment
audio = seg_pack(load("0929"), "audio", 0)      # local mp3 segment
text = seg_pack(load("1014"), "text", 0)        # CapCut 9.6 text segment
text["material"] = load("0920")["materials"]["texts"][0]  # Rubik-Bold, white + black stroke style
for x in video["extras"]:
    if x["category"] == "material_animations": x["object"]["animations"] = []
anims = {}
for p in ("0928 (2)", "0917"):
    for a in load(p)["materials"]["material_animations"]:
        for x in a["animations"]:
            if x["panel"] == "video" and x["name"] in ("Fade In", "Fade Out"):
                anims[x["name"]] = x
json.dump({"capcut_version": "9.6", "video": video, "audio": audio, "text": text, "animations": anims},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, "anims:", list(anims))
