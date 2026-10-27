# AutoEdit Long Form - notes for agents

- Folder is `YT Automation\AutoEditLongForm` (launcher `AutoEditLongForm.bat`). A short-form tool may later be a sibling (e.g. `AutoEditShortForm`) sharing `YT Automation\Library`; keep the Library layout stable. Code paths are all relative to the script, so folder renames need no code changes. Do NOT build the short-form tool until the user asks.
- User-facing docs: `GUIDE.md` (keep it in sync with settings/behaviour). User is non-technical; never automate the CapCut UI.

## When the user says "edit <content folder> with AutoEditLongForm"
1. Check the content folder has: `Pictures\` (NNNN_*.jpg), `Voice\Script N.mp3` (or Script mp3s in the root), the scene-by-scene guide `.md`, `Description.txt`, `Tags and keyword.txt`. Report anything missing.
2. Need the CapCut project name (the user creates an empty project first). CapCut must be closed (`tasklist | grep -i capcut`). Running the tool overwrites that project's timeline (a backup is kept in `_autoedit\backups`), so confirm first if the project already has an edit.
3. Run: `python autoedit.py "<content>" --project "<name>"` (first run transcribes the voice, about 40 s per minute of voice on CPU; run it in the background).
4. Read `_autoedit\report.txt` (warnings, alignment) and `<content>\YOUTUBE UPLOAD.txt`.
5. Review the upload text against the guide's script segments (the source of truth for what the video says):
   - every fact, number, name and date in the description must be said in the video
   - chapter names should fit their sections
   - deal with each `[TO DO]`: placeholders, links, off-topic tags
   - tighten weak lines; the first ~150 characters are the search snippet and must carry the main keyword
   Edit ONLY `YOUTUBE UPLOAD.txt`, never the user's Description.txt / Tags file. Note that re-running the tool regenerates YOUTUBE UPLOAD.txt.
6. Summarise for the user what was built, what you changed in the upload text, and what they still must do (links, credits are already included).
- After manual CapCut changes (music swapped etc.): `--upload-only --project "<name>"` re-makes the upload text from the real project (read-only).

## Technical
- `autoedit.py` writes CapCut 9.6 drafts directly (plain JSON). Projects: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\<name>\`.
  - Write `draft_content.json` (+ `.bak`, `template-2.tmp`) AND the copy in `Timelines\<main_timeline_id>\`.
  - Also update `draft_meta_info.json` (media pool), `draft_virtual_store.json` and `root_meta_info.json` (tm_duration).
- CapCut object shapes come from `templates/capcut_templates.json`, made by `tools/make_templates.py` from real CapCut-saved drafts.
  - Keyframe types verified in the CapCut 9.6 binaries and confirmed kept after a CapCut re-save: KFTypeScaleX, KFTypeAlpha.
  - Only `curveType: "Line"` is used; easing is approximated with 5 linear keyframes.
- Testing without touching real projects:
  - `--dry-run` writes to `<content>\_autoedit\dry_run\`, including its upload text.
  - Or copy an empty project folder to %TEMP%, change `draft_id` in its `draft_meta_info.json`, and run with `--project-dir <copy>`.
- Transcription: faster-whisper `small`, CPU int8 (CUDA cuBLAS missing on this laptop). Cached per voice file in `<content>\_autoedit\transcripts\` as `{size, model, words:[{w,s,e}]}`.
- Music:
  - Tracks live in `Library/Music/Informative/<Mood>` (Kevin MacLeod CC-BY). Avoid tracks tagged Humorous: the user wants informative, not meme.
  - Credit text is in `Library/Music/credits.json` (title = file name). `tools/get_music.py` keeps it up to date using incompetech's `pieces.json` catalog.
- Old `YT Automation\Sounds` must stay (old projects reference it).
