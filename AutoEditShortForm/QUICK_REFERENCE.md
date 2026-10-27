# Quick Reference Card

## 🚀 One-Line Commands

```bash
# Most common: Create viral clips with all effects
python autoshort.py "video.mp4"

# Check if everything works
python autoshort.py --check-deps

# 5 clips instead of 3
python autoshort.py "video.mp4" --clips 5

# Shorter 30-second clips
python autoshort.py "video.mp4" --duration 30

# Process entire folder
python autoshort.py --batch "videos/*.mp4"
```

---

## 📁 File Structure

```
AutoEditShortForm/
├── autoshort.py          # Main script - run this
├── settings.json         # Edit to customize
├── README.md            # Full documentation
├── QUICKSTART.md        # Setup guide
├── PHASE2_FEATURES.md   # Phase 2 details
├── requirements.txt     # Dependencies
└── tools/               # Advanced modules (Phase 2)
    ├── __init__.py
    ├── audio_analyzer.py
    ├── caption_generator.py
    ├── video_processor.py
    └── zoom_effects.py
```

---

## ⚙️ Key Settings

### Caption Style
```json
"captions": {
  "enabled": true,
  "color": "#FFD700",      // Yellow
  "font_size": 80,
  "uppercase": true
}
```

### Speed Control
```json
"speed": {
  "enabled": true,
  "fast": 1.75,    // Speed up boring parts
  "slow": 0.65     // Slow down highlights
}
```

### Zoom Control
```json
"zoom": {
  "enabled": true,
  "amount": 1.15   // 15% zoom
}
```

---

## 🎯 Phase 2 Features

| Feature | Status | What It Does |
|---------|--------|--------------|
| **Captions** | ✅ Live | Word-by-word animated yellow text |
| **Speed Ramping** | ✅ Live | Fast boring, slow highlights |
| **Zoom Effects** | ✅ Live | Punch in on reactions |
| **Silence Removal** | ✅ Live | Remove dead air |
| **Vertical Crop** | ✅ Live | 9:16 for TikTok/Shorts |
| **AI Highlights** | ✅ Live | Auto-detect best moments |
| **Batch Process** | ✅ Live | Multiple videos at once |
| **SRT Export** | ✅ Live | Subtitle files |

---

## 🔑 Trigger Keywords

**These words get:**
- Slow motion (0.65x)
- Zoom effect (1.15x)

```
oh my god, let's go, what the, no way, insane, 
crazy, holy, wow, sick, killed, dead, clutch, gg
```

---

## 📊 Output

### What You Get
```
Output/your_video_name/
├── clip_001_video.mp4    # Clip 1 (with all effects)
├── clip_002_video.mp4    # Clip 2 (with all effects)
├── clip_003_video.mp4    # Clip 3 (with all effects)
└── _metadata/
    ├── captions.srt      # Subtitle file
    └── clips_metadata.json # Details
```

### Each Clip Has
- ✅ Animated captions (word-by-word)
- ✅ Speed ramping (dynamic pacing)
- ✅ Zoom effects (on reactions)
- ✅ 9:16 vertical (TikTok ready)
- ✅ 1080x1920 resolution
- ✅ 30-60 seconds duration

---

## ⚡ Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "FFmpeg not found" | `winget install ffmpeg` |
| "Whisper not installed" | `pip install openai-whisper` |
| No captions showing | Check `settings.json` font path |
| Clips too long/short | Adjust `target_duration_s` |
| Speed too aggressive | Lower `fast`/`slow` values |
| Processing fails | Disable features one by one |

---

## 📞 Installation (First Time)

```bash
# 1. Install FFmpeg
winget install ffmpeg

# 2. Install Python packages
cd "C:\Users\chris\Desktop\YT Automation\AutoEditShortForm"
pip install -r requirements.txt

# 3. Test
python autoshort.py --check-deps

# 4. Run
python autoshort.py "your_video.mp4"
```

---

## 🎨 Caption Styles

### Viral (Default)
- Large gold text (#FFD700)
- Center screen
- Uppercase
- Pop animation

### Clean
- White text
- Bottom screen
- Normal case
- Fade animation

### Minimal
- Small white text
- Bottom screen
- No animation
- Basic subtitles

**Change style:**
```bash
python autoshort.py "video.mp4" --style clean
```

---

## 📈 Performance

| Task | Time |
|------|------|
| **Transcribe 1hr video** | 3-5 min |
| **Find highlights** | Instant |
| **Process 1 clip (Phase 2)** | 20-30 sec |
| **Total for 3 clips** | ~5 min |
| **Manual editing** | 2+ hours |
| **Time saved** | 95%+ |

---

## 💡 Pro Tips

1. **Best source:** 1080p+ video, clear audio
2. **Ideal length:** 30-60 seconds per clip
3. **Keywords matter:** Add custom ones in settings
4. **Test settings:** Start with defaults, tweak later
5. **Batch process:** Do multiple videos overnight
6. **SRT files:** Use for manual caption tweaks
7. **Metadata:** Check JSON for clip details

---

## 🔗 Quick Links

- **Main docs:** `README.md`
- **Setup guide:** `QUICKSTART.md`
- **Phase 2 details:** `PHASE2_FEATURES.md`
- **Config:** `settings.json`
- **Requirements:** `requirements.txt`

---

## 📋 Checklist

Before running:
- [ ] FFmpeg installed (`ffmpeg -version`)
- [ ] Python packages installed (`pip list`)
- [ ] Video file exists
- [ ] Settings.json edited (optional)

After running:
- [ ] Check Output folder
- [ ] Watch clips
- [ ] Check metadata JSON
- [ ] Adjust settings if needed
- [ ] Post to TikTok/Shorts!

---

**That's it! You're ready to create viral clips.** 🎬🚀

Run: `python autoshort.py "video.mp4"` and watch the magic happen!
