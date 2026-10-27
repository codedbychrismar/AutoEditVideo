# AutoEditShortForm

**Automatically convert long-form streamer/gaming videos into viral TikTok/YouTube Shorts with text commentary, captions, and smart editing.**

## What It Does

Takes a long video (streamer gameplay, podcast, reaction) and automatically creates viral short-form clips with:

✅ **Auto-generated animated captions** (word-by-word synced)  
✅ **Speed ramping** (fast-forward boring parts, slow-mo highlights)  
✅ **Smart cropping** (9:16 vertical, face/action tracking)  
✅ **Text commentary overlays** (engaging captions in viral style)  
✅ **Silence removal** (keeps only the good parts)  
✅ **Zoom effects** (emphasize key moments)  
✅ **Background music** (optional trending audio)  
✅ **Subtitle styling** (bold, colorful, attention-grabbing)

## Viral TikTok Editing Style

Based on successful gaming/streaming content creators, the style includes:

- **Fast-paced editing**: No dead air, constant engagement
- **Bold animated captions**: Yellow/white text with black outline, word-by-word animation
- **Speed variations**: 1.5-2x during setup, 0.5-0.75x during punchlines/reactions
- **Zoom punches**: Quick zoom-ins on key moments (kills, reactions, funny moments)
- **Text commentary**: Add context or reactions as on-screen text
- **Retention hooks**: First 3 seconds are crucial - cut straight to the action

## Installation

### Requirements
- Python 3.8+
- FFmpeg (for video processing)
- Whisper AI (for transcription/captions)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (if not already installed)
# Windows: Download from https://ffmpeg.org/ or use: winget install ffmpeg
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

## Usage

### Basic: Auto-generate clips from long video

```bash
python autoshort.py "path/to/your/long_video.mp4"
```

This will:
1. Transcribe the video
2. Find the best moments (based on audio energy, speech patterns)
3. Create 3-5 short clips (30-60 seconds each)
4. Add captions, speed ramping, and effects
5. Export as ready-to-post vertical videos

### Advanced: Custom settings

```bash
python autoshort.py "video.mp4" --clips 5 --duration 45 --style viral --captions bold
```

**Options:**
- `--clips N`: Number of clips to generate (default: 3)
- `--duration SECONDS`: Target duration per clip (default: 45)
- `--style`: Editing style (`viral`, `clean`, `minimal`)
- `--captions`: Caption style (`bold`, `subtle`, `none`)
- `--speed`: Enable speed ramping (default: true)
- `--zoom`: Enable zoom effects (default: true)
- `--commentary`: Add text commentary overlays (default: false)

### Manual: Provide specific timestamps

```bash
python autoshort.py "video.mp4" --timestamps "1:23-1:58,5:40-6:15,10:02-10:47"
```

## Folder Structure

```
AutoEditShortForm/
├── autoshort.py           # Main script
├── settings.json          # Global settings (caption style, effects, etc.)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # Caption templates and styles
│   ├── viral_captions.json
│   └── effects_presets.json
└── tools/                # Helper modules
    ├── transcribe.py     # Speech-to-text
    ├── highlight_finder.py   # Find best moments
    ├── video_processor.py    # FFmpeg wrapper
    └── caption_generator.py  # Create animated captions
```

## Workflow

### Input
Drop your long video (MP4, MOV, AVI) into a folder or specify the path.

### Processing
1. **Transcription**: Whisper AI generates word-level timestamps
2. **Analysis**: Detects highlights (loud moments, reactions, kills, laughter)
3. **Clip Selection**: Picks 3-5 best moments based on:
   - Audio energy peaks
   - Speech pattern changes (excitement, surprise)
   - Action keywords ("oh my god", "let's go", "what the", etc.)
4. **Editing**: For each clip:
   - Crop to 9:16 vertical (smart face/action tracking)
   - Add word-by-word animated captions
   - Apply speed ramping (slow mo highlights)
   - Add zoom punches on key moments
   - Remove silences/dead air
   - Optional: overlay text commentary
5. **Export**: Ready-to-post MP4 files

### Output
```
Output/
├── clip_001_highlight.mp4   (45 sec, 1080x1920)
├── clip_002_reaction.mp4    (38 sec, 1080x1920)
├── clip_003_win.mp4         (52 sec, 1080x1920)
└── _metadata/
    ├── timestamps.json      # Where each clip came from
    └── captions.srt         # Raw caption files
```

## Caption Styles

### Viral Style (Default)
- **Font**: Bold, thick stroke
- **Color**: Yellow (#FFD700) with black outline
- **Animation**: Pop in word-by-word
- **Position**: Center, large size
- **Effect**: Slight bounce on entry

### Clean Style
- **Font**: Modern sans-serif
- **Color**: White with subtle shadow
- **Animation**: Fade in phrase-by-phrase
- **Position**: Bottom third
- **Effect**: Smooth transitions

### Minimal Style
- **Font**: Simple, readable
- **Color**: White with black box background
- **Animation**: None (static)
- **Position**: Bottom
- **Effect**: None

## Settings (settings.json)

```json
{
  "captions": {
    "enabled": true,
    "style": "viral",
    "font_size": 72,
    "color": "#FFD700",
    "outline_color": "#000000",
    "outline_width": 4,
    "animation": "pop",
    "words_per_caption": 3,
    "position": "center"
  },
  "speed": {
    "enabled": true,
    "normal": 1.0,
    "fast": 1.75,
    "slow": 0.65,
    "detect_highlights": true
  },
  "zoom": {
    "enabled": true,
    "amount": 1.15,
    "duration_frames": 10,
    "on_keywords": true
  },
  "crop": {
    "aspect_ratio": "9:16",
    "track_face": true,
    "track_action": true
  },
  "silence_removal": {
    "enabled": true,
    "threshold_db": -40,
    "min_silence_ms": 500
  },
  "clip_selection": {
    "min_duration_s": 25,
    "max_duration_s": 60,
    "target_duration_s": 45,
    "energy_threshold": 0.6,
    "keyword_boost": true,
    "keywords": [
      "oh my god", "let's go", "what the", "no way",
      "insane", "crazy", "holy", "wow", "sick"
    ]
  },
  "output": {
    "resolution": "1080x1920",
    "fps": 30,
    "codec": "h264",
    "quality": "high",
    "format": "mp4"
  }
}
```

## Advanced Features

### Custom Commentary Text
Add your own text overlays:

```bash
python autoshort.py "video.mp4" --commentary "This was the craziest moment!,He didn't see that coming,Watch what happens next"
```

### Batch Processing
Process multiple videos at once:

```bash
python autoshort.py --batch "videos/*.mp4"
```

### CapCut Export (Optional)
Export timeline as CapCut project for manual tweaks:

```bash
python autoshort.py "video.mp4" --export-capcut
```

## Tips for Best Results

### Source Video Quality
- **Resolution**: 1080p or higher
- **Audio**: Clear voice, minimal background noise
- **Content**: High energy, reactions, exciting moments work best

### Content Types That Work Well
✅ Gaming highlights (kills, clutches, funny moments)  
✅ Streamer reactions  
✅ IRL moments  
✅ Debate/argument clips  
✅ Tutorial/how-to (condensed)  
✅ Podcast highlights  

### Optimization Tips
- **Hook first 3 seconds**: Tool automatically cuts to best moment
- **Keep it punchy**: 30-60 seconds is sweet spot for retention
- **Bold captions**: Makes content accessible + increases watch time
- **Speed variation**: Keeps viewer engaged, no dead air
- **Trending audio**: Consider adding trending sound if original audio isn't essential

## Troubleshooting

### "FFmpeg not found"
Install FFmpeg and add to PATH. See installation section.

### "Whisper model failed to load"
First run downloads AI models (~1GB). Requires internet connection.

### Clips too long/short
Adjust in settings.json: `clip_selection.target_duration_s`

### Captions not syncing
Check audio quality. Noisy audio = bad transcription. Use noise reduction first.

### Video quality loss
Increase output quality in settings.json: `output.quality: "highest"`

## Roadmap

- [ ] Auto-upload to TikTok/YouTube Shorts
- [ ] AI-generated hooks ("Wait for it...", "You won't believe this...")
- [ ] Emoji overlays on key moments
- [ ] Trending music auto-addition
- [ ] Multi-clip compilation (3 clips in one video)
- [ ] Voice-over generation (AI commentary)
- [ ] Face tracking zoom (zoom on streamer face during reactions)

## Credits

Inspired by viral TikTok creators like @ultragrand7 and top gaming clip channels.

Built for streamers, by streamers. 🎮

---

**Need help?** Create an issue or check the examples in `/examples`
