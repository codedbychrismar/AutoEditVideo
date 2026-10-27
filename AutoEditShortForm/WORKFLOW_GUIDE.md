# Workflow Guide - How to Use AutoEditShortForm

## Choose Your Workflow

There are **3 ways** to use AutoEditShortForm depending on your needs:

---

## 🚀 Workflow 1: FULLY AUTOMATIC (Recommended)

**Best for:** Quick viral clips, no manual editing needed

### Steps:
```bash
# 1. Put video anywhere on your computer
# Example: C:\Streams\my_stream.mp4

# 2. Run AutoEditShortForm
python autoshort.py "C:\Streams\my_stream.mp4"

# 3. Wait 5 minutes (for transcription + processing)

# 4. Get clips in Output folder!
# Output/my_stream/clip_001.mp4 ← Ready to post!
# Output/my_stream/clip_002.mp4
# Output/my_stream/clip_003.mp4
```

### What You Get:
- ✅ Animated captions (word-by-word)
- ✅ Speed ramping (auto fast/slow)
- ✅ Zoom effects (on reactions)
- ✅ 9:16 vertical crop
- ✅ 30-60 seconds each
- ✅ **100% ready to post to TikTok/Shorts**

### Time: ~5 minutes total
### Manual work: ZERO

**This is the default! Just run and go.** 🎉

---

## 🎬 Workflow 2: HYBRID (AI Finds Clips + You Edit in CapCut)

**Best for:** Want AI to find best moments, but manually add your style in CapCut

### Steps:

**Part A: Get Timestamps**
```bash
# 1. AI finds the best moments and gives you timestamps
python autoshort.py "C:\Streams\my_stream.mp4" --timestamps-only

# 2. Check Output folder:
# Output/my_stream/CAPCUT_TIMESTAMPS.txt
```

**CAPCUT_TIMESTAMPS.txt looks like:**
```
CLIP 1
  Start:    2:15.40  (135.40s)
  End:      2:48.70  (168.70s)
  Duration: 33.3 seconds
  Content:  OH MY GOD that was insane let's go clutch!
  Score:    1.85

CLIP 2
  Start:    5:42.10  (342.10s)
  End:      6:18.30  (378.30s)
  Duration: 36.2 seconds
  Content:  NO WAY did I just do that holy!
  Score:    1.72
```

**Part B: Edit in CapCut**
```
1. Open CapCut
2. Import your full video (my_stream.mp4)
3. Open CAPCUT_TIMESTAMPS.txt
4. For each clip:
   - Go to Start time (2:15.40)
   - Press 'S' to split
   - Go to End time (2:48.70)
   - Press 'S' to split
   - Delete everything except that segment
   - Crop to 9:16 (CapCut has preset)
   - Add captions (CapCut auto-captions)
   - Add effects, zooms, etc.
5. Export!
```

### Time: 
- AI finds moments: 3 minutes
- Manual CapCut editing: 10-15 minutes per clip

### Manual work: Medium (but AI did the hard part - finding moments!)

---

## 🎥 Workflow 3: FULLY MANUAL (Traditional)

**Best for:** Complete control, unique editing style

### Steps:
```
1. Watch entire stream
2. Mark timestamps manually
3. Import to CapCut/Premiere
4. Cut clips
5. Add effects, captions, transitions
6. Export
```

### Time: 2+ hours
### Manual work: Everything

**Not recommended - but AutoEditShortForm can help find moments!**

---

## 📁 Folder Organization (Recommended)

Create this structure for easy workflow:

```
YT Automation/
├── AutoEditShortForm/       # The tool
│   ├── autoshort.py
│   └── settings.json
│
├── Streams/                 # Your source videos
│   ├── stream_jan_15.mp4
│   ├── stream_jan_16.mp4
│   └── stream_jan_17.mp4
│
└── AutoEditShortForm/Output/  # Auto-created clips
    ├── stream_jan_15/
    │   ├── clip_001.mp4    ← Post these!
    │   ├── clip_002.mp4
    │   └── clip_003.mp4
    └── stream_jan_16/
        └── clip_001.mp4
```

---

## 💡 Which Workflow Should You Use?

### Use Workflow 1 (Fully Automatic) if:
- ✅ You want fastest results
- ✅ You're okay with AI-generated effects
- ✅ You post daily/frequently
- ✅ You trust the viral caption style
- ✅ You want zero editing work

### Use Workflow 2 (Hybrid) if:
- ✅ You want AI to find best moments
- ✅ But you have a unique editing style
- ✅ You want to add personal touches
- ✅ You're familiar with CapCut
- ✅ You have 15 min per clip to spare

### Use Workflow 3 (Manual) if:
- ✅ You're very picky about editing
- ✅ You have lots of time
- ✅ You're building a brand-specific style
- ✅ AutoEditShortForm isn't quite right for you

**Most users should start with Workflow 1, then try Workflow 2 if needed.**

---

## 🔄 Daily Streamer Workflow

### Morning Routine (5 minutes):
```bash
# 1. Export yesterday's VOD
# Twitch/YouTube: Download as MP4

# 2. Run AutoEditShortForm
python autoshort.py "yesterdays_stream.mp4" --clips 5

# 3. Get coffee while it processes ☕
# (Takes ~5 minutes for 2-hour stream)

# 4. Check Output folder
# Output/yesterdays_stream/clip_001.mp4 to clip_005.mp4

# 5. Watch clips, pick best 3

# 6. Post throughout the day:
#    - Clip 1: 10am
#    - Clip 2: 2pm  
#    - Clip 3: 7pm
```

### Result:
- 3 viral clips per day
- 5 minutes of work
- Consistent content schedule
- Algorithm loves you 📈

---

## 🎯 Advanced Workflows

### Batch Processing (Multiple Streams)
```bash
# Process all streams from this week
python autoshort.py --batch "C:\Streams\week_01_*.mp4"

# Result: Clips for every video automatically
```

### Custom Clips Count
```bash
# Get 10 clips instead of 3
python autoshort.py "stream.mp4" --clips 10

# Perfect for: Finding the ABSOLUTE best moment
```

### Different Duration
```bash
# Make 30-second clips (shorter = more viral)
python autoshort.py "stream.mp4" --duration 30

# Make 60-second clips (longer = more story)
python autoshort.py "stream.mp4" --duration 60
```

---

## 📤 After Generation: Posting Workflow

### Quick Post (Mobile)
```
1. AirDrop/Send clips to phone
2. Open TikTok/YouTube Shorts
3. Upload clip
4. Add hashtags
5. Post!
```

### Advanced Post (Desktop)
```
1. Open TikTok/YouTube on desktop
2. Upload clip
3. Add description (AI can generate in future)
4. Schedule posts
5. Track analytics
```

### Caption Ideas (From Clips)
```
AutoEditShortForm saves the text in metadata:
- "OH MY GOD that was insane let's go clutch!"
  → Caption: "CLUTCH MOMENT 🔥 #gaming #shorts"

- "This is the craziest play I've ever seen"
  → Caption: "I still can't believe this happened 😱"
```

---

## 🔧 Workflow Customization

### Settings for Different Content Types

**Gaming/Reactions (High Energy)**
```json
{
  "captions": {"uppercase": true, "font_size": 80},
  "speed": {"fast": 1.75, "slow": 0.65},
  "zoom": {"enabled": true, "amount": 1.15}
}
```

**Tutorials/Calm Content**
```json
{
  "captions": {"uppercase": false, "font_size": 60},
  "speed": {"fast": 1.3, "slow": 0.85},
  "zoom": {"enabled": false}
}
```

**Podcast Clips**
```json
{
  "captions": {"style": "clean", "position": "bottom"},
  "speed": {"fast": 1.5, "slow": 0.8},
  "clip_selection": {"target_duration_s": 60}
}
```

---

## 🎬 Comparison Table

| Feature | Workflow 1 (Auto) | Workflow 2 (Hybrid) | Workflow 3 (Manual) |
|---------|------------------|---------------------|---------------------|
| **Time** | 5 min | 20 min | 2+ hours |
| **Captions** | ✅ Auto | Manual in CapCut | Manual |
| **Speed Effects** | ✅ Auto | Manual | Manual |
| **Zoom Effects** | ✅ Auto | Manual | Manual |
| **Finding Moments** | ✅ AI | ✅ AI | Manual |
| **Customization** | Settings.json | Full CapCut control | Full control |
| **Best For** | Daily posts | Unique style | Brand building |

---

## 💰 ROI Comparison

### Manual Editing (Traditional)
- **Time**: 30 min per clip
- **Clips per day**: 2-3 max
- **Weekly output**: 14-21 clips
- **Cost**: Your time

### AutoEditShortForm Workflow 1
- **Time**: 5 min total
- **Clips per day**: 3-10+
- **Weekly output**: 21-70 clips
- **Cost**: Free (just electricity)

**Time saved: 90%+**
**Output increase: 300%+**

---

## 📝 Example Daily Schedule

### For Streamers:

**9:00 AM** - Export yesterday's VOD
```bash
python autoshort.py "vod_jan_15.mp4" --clips 5
```

**9:05 AM** - Go make breakfast (processing happens)

**9:10 AM** - Back, clips are ready!

**9:15 AM** - Watch 5 clips, pick best 3

**9:20 AM** - Upload Clip 1 to TikTok (scheduled for 10am)

**9:22 AM** - Upload Clip 2 to TikTok (scheduled for 2pm)

**9:24 AM** - Upload Clip 3 to TikTok (scheduled for 7pm)

**9:25 AM** - Done! Start your day. 🎉

**Total work time: 25 minutes**
**Content created: 3 viral clips**
**Manual editing avoided: 90 minutes**

---

## 🚀 Getting Started (First Time)

### Today:
```bash
# 1. Pick one old stream/video
python autoshort.py "old_stream.mp4"

# 2. Check the output
# Is it good? Great!
# Not perfect? Adjust settings.json

# 3. Run again with tweaked settings
python autoshort.py "old_stream.mp4"

# 4. Once happy, automate daily!
```

### Tomorrow and Beyond:
```bash
# Daily routine (5 minutes):
python autoshort.py "yesterdays_stream.mp4"
# Post clips, repeat.
```

---

## ❓ FAQ

**Q: Do I need CapCut at all?**
A: No! Workflow 1 is 100% automatic. Only use CapCut if you want manual control (Workflow 2).

**Q: Can I edit the clips after generation?**
A: Yes! The clips are normal MP4 files. Open in any editor.

**Q: What if I don't like the caption style?**
A: Change `settings.json` → `captions.color`, `font_size`, etc.

**Q: Can I turn off captions/zoom/speed?**
A: Yes! In `settings.json`, set `"enabled": false` for any feature.

**Q: How do I process multiple videos?**
A: Use `--batch`: `python autoshort.py --batch "folder/*.mp4"`

---

## 🎉 Summary

**Recommended for most users:**
1. Use **Workflow 1** (Fully Automatic)
2. Run daily after streams
3. Post 3 clips throughout the day
4. Watch your audience grow 📈

**Total time investment: 5 minutes per day**
**Output: 3 viral clips per day = 90 per month**

**That's the power of automation!** 🚀

---

**Ready to start?**

```bash
python autoshort.py "your_video.mp4"
```

**Let the clips roll!** 🎬✨
