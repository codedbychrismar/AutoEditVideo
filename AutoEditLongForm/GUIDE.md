# AutoEdit Long Form - How To Use

AutoEdit Long Form builds the whole CapCut timeline for a long-form (16:9, multi-minute) video. A separate short-form tool can live next to it later and share the same `Library\`.

It builds:

- images cut exactly on the spoken words
- a smooth 100% to 120% zoom on every image
- labels (names, dates, numbers, title, subscribe)
- informative background music that changes with the mood
- sound effects
- voice level

You only create an empty CapCut project and run AutoEdit. You never type timings by hand.

---

## 1. Where everything lives

```
YT Automation\
├── AutoEditLongForm\            <- the long-form tool (open this folder to run it)
│   ├── AutoEditLongForm.bat     <- double-click (or drag a content folder onto it)
│   ├── autoedit.py              <- the program
│   ├── settings.json            <- zoom, music volume, text size, sound levels ...
│   ├── GUIDE.md                 <- this file
│   ├── templates\               <- CapCut building blocks (do not edit)
│   └── tools\get_music.py       <- downloads / refreshes the music library
│
└── Library\                     <- shared by every channel, every video (long and short form)
    ├── Music\
    │   ├── Informative\
    │   │   ├── Curious\         <- light intrigue, discovery (default)
    │   │   ├── Calm\            <- thoughtful explaining, reflection
    │   │   ├── Mystery\         <- "but here's the catch", warnings, debates
    │   │   ├── Historical\      <- ancient / period flavour (Egypt, Victorian ...)
    │   │   ├── Serious\         <- war, loss, tragedy
    │   │   └── Upbeat\          <- light positive moments, endings, CTAs
    │   └── CREDITS.txt
    ├── SFX\
    │   ├── Whoosh\  Pop\  Ding\  Riser\  Camera\  Impact\
    │   └── Meme\                <- NOT used automatically (only if you ask for it)
    └── Fonts\Rubik-Bold.ttf
```

To add music, drop any `.mp3` into a mood folder and it will be used automatically. The same goes for sound effects: drop them into a category folder.

All bundled music is by Kevin MacLeod (CC BY 4.0). It is free for YouTube, but **you must credit it**. AutoEdit puts the exact credit lines for the music used into the description in `YOUTUBE UPLOAD.txt` automatically.

Your old `YT Automation\Sounds` folder was left untouched, so old CapCut projects still find their files.

---

## 2. How to set up each content folder

```
Content 11 - War Dog - (EDIT)\
├── Pictures\        0001_xxx.jpg, 0002_xxx.jpg, ...   (number = beat number in the guide)
├── Voice\           Script 1.mp3, Script 2.mp3, ...   (in speaking order)
├── SFX\             (optional) extra sounds just for this video
├── war_dog_scene_by_scene_image_prompts.md            (the guide)
├── Description.txt                                    (your YouTube description draft)
└── Tags and keyword.txt                               (tags line + pinned comment options)
```

**Rules**

| What | Rule |
|---|---|
| Pictures | The file name must START with the beat number: `0001_...jpg`, `0002_...jpg`. `.jpg .jpeg .png .webp` all work. A missing number means the previous image stays on screen longer. |
| Voice | Any number of files. They are placed back-to-back in name order (`Script 1`, `Script 2`, ... `Script 10`). `.mp3 .wav .m4a`. Old layout (Script files next to the guide, no Voice folder) also still works. |
| Guide | The same format you already use: `## SECTION 1: NAME (...)`, `### Beat 1 - ...`, `**Script Segment:** "..."`, `- **Action:** ...`, `- **Mood:** ...`. The script segments must match what the voice actually says. |
| Title | Keep the title line `## "How Did Humans Invent the Comb?"` near the top of the guide. It is used for the big title text and the YouTube title. |
| Description.txt | Your normal description: hook, summary, `TIMESTAMPS` list, sources, other videos, hashtags, closing line. The timestamps can be the guess from the guide; AutoEdit fixes them to the real edit. Don't add music credits; they are added automatically. |
| Tags and keyword.txt | One line of comma-separated tags (most important first), then a line containing "Pinned Comment" followed by your options. This is the same layout you already use. |

AutoEdit creates an `_autoedit\` folder inside the content folder for its own files: transcripts, labels, report, backups and credits. It also creates **`YOUTUBE UPLOAD.txt`** next to your files (see section 4).

---

## 3. Making a video (every time)

1. Put the files into the content folder as shown above.
2. Open CapCut and click **Create project**. Rename it if you like, for example `WAR DOG`. Add nothing, then **close CapCut completely**.
3. **Drag the content folder onto `AutoEditLongForm.bat`**, or double-click it and paste the folder path.
4. Pick the CapCut project from the list. The newest project is number 1.
5. Wait. The first run transcribes the voice, which takes about 6–7 minutes for a 10-minute video. Re-runs take under a minute.
6. Open CapCut and open the project. The timeline is done.
7. Read `_autoedit\report.txt` for warnings (for example "image missing", "beat timing uncertain").
8. Open **`YOUTUBE UPLOAD.txt`** in the content folder. It has the title, description, tags and pinned comment ready to paste. Fix anything under `[TO DO]` first.

From a terminal it works the same: `python autoedit.py "C:\...\Content 11 - War Dog - (EDIT)" --project "WAR DOG"`

**Or just ask Devin**, for example: *"Edit Content 11 - War Dog - (EDIT) with AutoEditLongForm, CapCut project WAR DOG."* Devin will:
1. check the folder (Pictures, Voice, guide .md, Description.txt, Tags and keyword.txt)
2. run the edit and read the report
3. review the description, tags and pinned comments against the script, and fix wrong facts, placeholders and weak lines
4. tell you what to check

Devin edits only `YOUTUBE UPLOAD.txt`, never your original Description.txt or Tags file.

**Every run rebuilds the timeline from scratch.** If you edit by hand in CapCut and then run AutoEdit again, those hand edits are replaced. A backup of the previous version is kept in `_autoedit\backups\`, which holds the last 5 runs. Best practice is to fix labels and sounds through the files below and re-run, then do any final hand-polish in CapCut last.

Useful extra options:
- `--upload-only` re-makes only `YOUTUBE UPLOAD.txt` from the CapCut project as it is now, without changing the edit. Use it after you changed music or moved things by hand in CapCut, so the credits and chapters still match.
- `--dry-run` checks everything and touches nothing in CapCut. Its upload file goes to `_autoedit\dry_run\`.
- `--reset-texts` throws away your edited labels and re-creates them from the guide.
- `--retranscribe` listens to the voice again, for example after you replaced a voice file.

---

## 4. YouTube upload text, labels, sounds and settings

### `YOUTUBE UPLOAD.txt` (made every run)

Built from your Description.txt, Tags and keyword.txt, the guide and the finished edit:

| Part | What AutoEdit does |
|---|---|
| Title | Taken from the guide's title line. Warns if it's over YouTube's 100-character limit. |
| Chapters | Re-times every `0:00 Name` line to when that section really starts in the edit. The guide's estimates are often 10–45 s off. Makes sure the first is 0:00, there are at least 3, and each is 10+ s long (otherwise YouTube hides all chapters). If you wrote none, it creates them from the guide sections. |
| Music credits | Adds the exact credit lines for the music actually in the CapCut project, and removes old or duplicate credit lines. |
| Tags | Removes duplicates, puts the title first, and trims to YouTube's 500-character limit, dropping the last (least important) tags first. Flags tags whose words never appear in the video. |
| Checks | Flags placeholders like `[Cat video link]`, "check out" video titles without links, too many hashtags, descriptions over 5000 characters, and `<` `>` characters (not allowed). |

Music credit text lives in `Library\Music\credits.json`. If you add your own music, add its credit there with the same layout.

### Labels: `<content>\_autoedit\texts.json`

These are created automatically on the first run:
- people's names, with their role taken from the script ("Madeleine Mumcuoglu / Research associate at Hebrew University")
- dates and numbers ("~3,700 YEARS OLD", "4000–3500 BCE", "APRIL 1869", "19TH CENTURY")
- the title question
- "HIT THE LIKE BUTTON" and "SUBSCRIBE & COMMENT"

After that the file is yours. Edit it in Notepad and re-run:

```json
{"beat": 21, "at": "Seventeen letters", "text": "17 LETTERS · 7 WORDS", "pos": "lower"},
{"beat": 19, "at": "Madeleine", "text": "MADELEINE MUMCUOGLU|Hebrew University", "pos": "lower"}
```

| Field | Meaning |
|---|---|
| `beat` | Beat number from the guide. |
| `at` | Word(s) from that beat's script. The label pops in exactly when they are spoken. |
| `text` | What shows. `\|` starts a smaller second line, such as a job title. |
| `pos` | `lower` (default, lower third), `upper`, `right` / `left` (beside a centred host), or `center`. |

Delete an entry to remove that label. Labels are checked automatically and shrunk if they would go outside the frame.

### Extra sound effects: `<content>\_autoedit\extra_sfx.json`

```json
{"sounds": [
  {"beat": 27, "at": "lice", "sound": "Impact"},
  {"beat": 96, "at": "awarded", "sound": "Meme/Bruh.mp3", "volume_db": -3}
]}
```

`sound` is either a category folder (`Whoosh`, `Pop`, `Ding`, `Riser`, `Camera`, `Impact`), which picks a random file, or a file inside `Library\SFX`.

### Automatic sound effects (no work needed)

| When | Sound |
|---|---|
| New guide section | Whoosh |
| Section named ANSWER / CONCLUSION / REVEAL / VERDICT | Riser that builds into it |
| Every label | Soft pop |
| Subscribe / like button | Ding |
| Image description mentions a check-mark, phone screen / photo, or explosion / spark | Matching sound |

### Settings: `AutoEditLongForm\settings.json`

| Setting | Default | What it does |
|---|---|---|
| `zoom.min` / `zoom.max` | 1.00 / 1.20 | Zoom range (100% to 120%). Images alternate zoom-in / zoom-out. |
| `zoom.easing` | `ease` | Smooth start and stop. `linear` = constant speed. |
| `zoom.fill_frame` | true | Removes thin black bars on images that aren't exactly 16:9. |
| `music.under_voice_db` | 22 | Music this many dB quieter than the voice. 18 = louder, 26 = quieter. |
| `music.mood_keywords` | ... | Which guide words choose which music mood. |
| `sfx.levels_db` | ... | Loudness per sound category. |
| `text.label_scale` | 0.62 | Label size. |
| `voice.target_db` | -16 | Voice is raised toward this, never past -1.5 dB peaks. |

To change one video only, create `<content>\_autoedit\settings.json` with only the part you want, for example `{"zoom": {"max": 1.10}}`.

---

## 5. Editing style for faceless explainer videos (research summary)

This is how successful narrated, stickman-style and documentary channels are edited. ✅ means AutoEdit does it for you; ✍️ means it's up to you when you write the script and image prompts.

**Pacing**
- ✅ **Cut on the word.** The picture changes the moment the narration introduces the new thing. Visuals that land slightly before or exactly on the word are remembered better.
- ✍️ **One image every 4–6 seconds on average.** That is about 100–150 images for 10 minutes. Use 2–3 s for reveals and twists, and up to 8–12 s only for a quote or a moment that should breathe. **Never hold one image longer than about 12 s.** AutoEdit warns you in the report when this happens; add an extra beat or image there.
- ✍️ **Hook harder than everything else.** The first 30–60 s should have the fastest cuts and a question the viewer wants answered within about 5 s.
- ✅ **Pattern interrupt every 45–90 s.** Music changes, section whooshes, title cards and labels do this. Don't overdo it: random meme sounds and fake energy spikes hurt retention in informative videos.

**Motion**
- ✅ **Ken Burns zoom of 10–20% per shot**, alternating in and out, **with easing.** Linear zooms look amateur. Under about 8% is invisible; over about 30% the viewer watches the camera instead of the picture.
- ✍️ Keep important details away from the outer ~10% of each image, because the 120% zoom crops it.

**Text on screen**
- ✅ **Few words, not the narration.** Use names, dates, numbers and key terms. Repeating the spoken sentence on screen overloads viewers.
- ✅ Keep each label up long enough to read (about 1.5–3 s per line), and keep it off the frame edges.
- ✍️ Quotes from real people work well as on-screen quote cards. Add them in `texts.json`.

**Sound**
- ✅ **Music bed about 18–24 dB under the voice**, constant, with no pumping or ducking. Documentary channels measure 24–31 dB under. It sounds almost too quiet while editing and is right for viewers.
- ✅ **Never total silence.** On a faceless channel, silence feels like the video broke, so the music runs from start to end.
- ✅ **Music changes character as the story moves** (mood per section), with crossfades instead of hard cuts.
- ✅ **Sound effects are few and on the exact word**, as signals: section change, a fact popping up, a reveal. Short hits can be closer to the voice than the music.
- ✍️ Optional: in CapCut, select the 3 voice clips and use **Audio > Normalize loudness** for a slightly louder final mix. AutoEdit can only raise the voice until its peaks hit the limit.

**Structure** (when writing scripts)
- ✍️ Cold open with a concrete question or image (15–30 s), then context with one clear stake, then 3–5 story beats that each end on a small cliffhanger, then a resolution that pays off the opening, then a call to the next video (10–20 s).
- ✍️ A 10-minute video is about 1,500–1,700 words of narration.
- ✍️ A mid-video like/subscribe ask works best early and short. AutoEdit adds a label and a ding automatically.

**Optional extras in CapCut** (manual)
- **Captions:** CapCut > Text > Auto captions. Many faceless channels use burned-in captions because a lot of people watch muted.
- **Chapters:** ✅ done automatically in `YOUTUBE UPLOAD.txt`. Chapters help viewers jump around and show up in Google search.

Sources: umbrellacreators.com (measured music levels of narrated stickman/documentary channels), facelesschannel.com (faceless pacing), 43frames.com (Ken Burns values), prepublish.ai (pattern interrupts), teachers.institute (Mayer's redundancy principle for on-screen text).

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| "CapCut is open" | Close CapCut fully (check the system tray), then run again. |
| Project not in the list | Create it in CapCut first, close CapCut, run again. |
| "Less than 60% of the script matched" | The guide doesn't match the voice (wrong file or a rewritten script). Fix the guide. |
| A beat starts slightly early or late | Usually the voice changed a word compared with the guide. Update the guide text and run with `--retranscribe` if you replaced the voice. |
| Labels look too big or small | Change `text.label_scale` in settings.json. |
| Music too loud or quiet | Change `music.under_voice_db` (bigger number = quieter). |
| Want the old meme-style sounds | Add them in `extra_sfx.json` with `"sound": "Meme/vine-boom.mp3"`. |
| Something went wrong | Your previous timeline is in `_autoedit\backups\`. Copy `draft_content.json` back into the CapCut project folder while CapCut is closed. |

Requirements (already installed on this laptop): Python 3 with `faster-whisper`, `av`, `numpy` and `pillow`. The speech model downloads automatically the first time.
