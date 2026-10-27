# Quick Start Guide - AutoEditShortForm

## 1. Install Dependencies

### Install FFmpeg
**Windows:**
```powershell
winget install ffmpeg
```
Or download from: https://ffmpeg.org/download.html

**Verify installation:**
```bash
ffmpeg -version
```

### Install Python packages
```bash
pip install -r requirements.txt
```

This will install:
- `openai-whisper` (AI transcription)
- `numpy` (data processing)

**Note:** First run will download Whisper AI models (~500MB)

---

## 2. Basic Usage

### Test Installation
```bash
python autoshort.py --check-deps
```

Should show:
```
✓ FFmpeg found
✓ Whisper AI found
✓ NumPy found
✅ All dependencies installed!
```

### Create Your First Clip
```bash
python autoshort.py "path/to/your/streamer_video.mp4"
```

**What happens:**
1. Transcribes the video (may take 2-5 minutes for a 1-hour video)
2. Finds the 3 best moments (based on keywords, excitement)
3. Creates 3 short clips (30-60 seconds each)
4. Crops to vertical 9:16 format
5. Outputs to `Output/[video_name]/`

---

## 3. Common Usage Examples

### Generate 5 clips instead of 3
```bash
python autoshort.py "video.mp4" --clips 5
```

### Make shorter clips (30 seconds each)
```bash
python autoshort.py "video.mp4" --duration 30
```

### Process multiple videos
```bash
python autoshort.py --batch "videos/*.mp4"
```

### Change caption style
```bash
python autoshort.py "video.mp4" --style clean
```

Styles: `viral` (default), `clean`, `minimal`

---

## 4. Check Your Output

After processing, check:
```
Output/
└── your_video_name/
    ├── clip_001_your_video_name.mp4  ← Ready to post!
    ├── clip_002_your_video_name.mp4
    ├── clip_003_your_video_name.mp4
    └── _metadata/
        └── clips_metadata.json        ← Timestamps & info
```

Each clip is:
- **9:16 vertical** (1080x1920) for TikTok/Shorts
- **30-60 seconds** (optimal for retention)
- **Best moments** (keyword-detected highlights)

---

## 5. Customize Settings

Edit `settings.json` to change:

### Clip Selection Keywords
Add your own trigger words:
```json
"keywords": [
  "oh my god",
  "let's go",
  "YOUR_CUSTOM_WORD"
]
```

### Target Duration
```json
"target_duration_s": 45
```

### Output Quality
```json
"quality": "high"  // or "highest", "medium"
```

---

## 6. Tips for Best Results

### ✅ Good Source Videos
- Clear audio (minimal background noise)
- High energy moments (reactions, wins, fails)
- Streamer commentary or gaming highlights
- 720p+ resolution

### ❌ Difficult Source Videos
- Heavy background music (masks voice)
- Multiple people talking over each other
- Very long quiet sections
- Poor audio quality

### Optimization
- **Gaming:** Kills, clutches, funny fails work best
- **Reactions:** Strong emotions, surprises
- **IRL/Podcasts:** Controversial takes, arguments, jokes

---

## 7. Troubleshooting

### "FFmpeg not found"
- **Fix:** Install FFmpeg and restart terminal
- **Verify:** Run `ffmpeg -version`

### "Whisper model failed to load"
- **Fix:** First run downloads models (~500MB), needs internet
- **Alternative:** Use smaller model: edit `transcription.model_size: "tiny"`

### Clips are boring/wrong moments
- **Fix:** Adjust keywords in settings.json
- **Fix:** Lower `energy_threshold` to find more moments
- **Fix:** Manually specify timestamps (coming soon)

### Video quality is bad
- **Fix:** Change quality in settings.json: `"quality": "highest"`
- **Fix:** Ensure source video is 1080p+

### Transcription is wrong
- **Fix:** Use better audio (reduce background noise first)
- **Fix:** Use larger Whisper model: `"model_size": "medium"`

---

## 8. What's Next?

Current version is **Phase 1**: Basic clip extraction + vertical crop

**Coming in Phase 2:**
- ✨ Animated captions (word-by-word)
- ⚡ Speed ramping (fast-forward boring parts)
- 🔍 Zoom effects (on key moments)
- 🔇 Silence removal (no dead air)
- 🎵 Background music overlay
- 🎨 Text commentary overlays

**Phase 3:**
- Auto-upload to TikTok/YouTube
- Face tracking for smart crops
- AI-generated hooks
- Emoji reactions
- Trending audio addition

---

## 9. Workflow Recommendation

### For Streamers:
1. **Record stream** (OBS, Streamlabs)
2. **Run AutoEditShortForm** on full VOD
3. **Get 3-5 best clips** automatically
4. **Post to TikTok/Shorts** (add final touches in TikTok editor if needed)
5. **Repeat daily** for consistent content

### Time Saved:
- Manual editing: **30-60 minutes per clip**
- AutoEditShortForm: **5-10 minutes total** (mostly transcription)
- **Savings: 90%+ of editing time**

---

## Support

**Issues?** Check:
1. This guide
2. README.md (detailed documentation)
3. settings.json (all options explained)

**Feature requests?** Add to roadmap in README.md

---

Happy clipping! 🎬🚀
