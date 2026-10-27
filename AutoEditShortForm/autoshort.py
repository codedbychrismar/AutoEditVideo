r"""AutoEditShortForm - Convert long videos into viral TikTok/Shorts clips.

Usage:
    python autoshort.py "path/to/video.mp4"
    python autoshort.py "video.mp4" --clips 5 --duration 45 --style viral
    
Converts streamer/gaming long-form content into short viral clips with:
- Auto captions (word-by-word synced)
- Speed ramping
- Smart cropping (9:16 vertical)
- Zoom effects
- Silence removal
"""

import argparse
import json
import os
import sys
import subprocess
import glob
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))

def log(*args):
    print(*args, flush=True)


def check_dependencies():
    """Check if required tools are installed."""
    log("Checking dependencies...")
    
    # Check FFmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log("✓ FFmpeg found")
        else:
            log("✗ FFmpeg not working properly")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        log("✗ FFmpeg not found")
        log("  Install: https://ffmpeg.org/ or 'winget install ffmpeg'")
        return False
    
    # Check Python dependencies
    try:
        import whisper
        log("✓ Whisper AI found")
    except ImportError:
        log("✗ Whisper not installed")
        log("  Install: pip install openai-whisper")
        return False
    
    try:
        import numpy
        log("✓ NumPy found")
    except ImportError:
        log("✗ NumPy not installed")
        log("  Install: pip install numpy")
        return False
    
    return True


def load_settings():
    """Load settings from settings.json."""
    settings_path = os.path.join(HERE, "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        log("⚠️  settings.json not found, using defaults")
        return get_default_settings()


def get_default_settings():
    """Return default settings."""
    return {
        "captions": {
            "enabled": True,
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
            "enabled": True,
            "normal": 1.0,
            "fast": 1.75,
            "slow": 0.65,
            "detect_highlights": True
        },
        "zoom": {
            "enabled": True,
            "amount": 1.15,
            "duration_frames": 10,
            "on_keywords": True
        },
        "crop": {
            "aspect_ratio": "9:16",
            "track_face": True,
            "track_action": True
        },
        "silence_removal": {
            "enabled": True,
            "threshold_db": -40,
            "min_silence_ms": 500
        },
        "clip_selection": {
            "min_duration_s": 25,
            "max_duration_s": 60,
            "target_duration_s": 45,
            "energy_threshold": 0.6,
            "keyword_boost": True,
            "keywords": [
                "oh my god", "let's go", "what the", "no way",
                "insane", "crazy", "holy", "wow", "sick",
                "bruh", "damn", "dude", "wait", "look at"
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


def get_video_info(video_path):
    """Get video duration, resolution, etc using FFprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-count_packets",
            "-show_entries", "stream=width,height,duration,nb_read_packets",
            "-of", "json",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            stream = info['streams'][0]
            return {
                'width': int(stream.get('width', 1920)),
                'height': int(stream.get('height', 1080)),
                'duration': float(stream.get('duration', 0)),
                'frames': int(stream.get('nb_read_packets', 0))
            }
    except Exception as e:
        log(f"⚠️  Could not get video info: {e}")
    
    return {'width': 1920, 'height': 1080, 'duration': 0, 'frames': 0}


def transcribe_video(video_path, model_size="base"):
    """Transcribe video using Whisper AI."""
    log(f"\n🎤 Transcribing video (this may take a few minutes)...")
    
    try:
        import whisper
        
        # Load model
        log(f"   Loading Whisper model: {model_size}")
        model = whisper.load_model(model_size)
        
        # Transcribe with word-level timestamps
        log("   Processing audio...")
        result = model.transcribe(
            video_path,
            word_timestamps=True,
            language="en"
        )
        
        log(f"✓ Transcription complete ({len(result['segments'])} segments)")
        return result
        
    except Exception as e:
        log(f"✗ Transcription failed: {e}")
        return None


def find_highlights(transcription, video_info, settings):
    """Find the best moments in the video for clips."""
    log("\n🔍 Finding highlights...")
    
    if not transcription or 'segments' not in transcription:
        log("✗ No transcription data available")
        return []
    
    highlights = []
    clip_settings = settings['clip_selection']
    keywords = [kw.lower() for kw in clip_settings['keywords']]
    
    # Analyze each segment
    for i, segment in enumerate(transcription['segments']):
        text = segment['text'].lower().strip()
        start = segment['start']
        end = segment['end']
        duration = end - start
        
        # Skip very short segments
        if duration < 3:
            continue
        
        # Calculate "interest score"
        score = 0.0
        
        # Check for keywords (excitement indicators)
        for keyword in keywords:
            if keyword in text:
                score += 1.0
                break
        
        # Check for high word density (fast talking = excitement)
        words = text.split()
        words_per_second = len(words) / duration if duration > 0 else 0
        if words_per_second > 2.5:  # Fast talking
            score += 0.5
        
        # Check for punctuation (questions, exclamations)
        if '!' in segment['text'] or '?' in segment['text']:
            score += 0.3
        
        # Check for capital words (shouting transcription)
        if any(word.isupper() and len(word) > 2 for word in segment['text'].split()):
            score += 0.4
        
        if score >= clip_settings['energy_threshold']:
            highlights.append({
                'start': max(0, start - 2),  # Add 2s buffer before
                'end': min(video_info['duration'], end + 2),  # Add 2s buffer after
                'text': segment['text'].strip(),
                'score': score
            })
    
    # Sort by score (best first)
    highlights.sort(key=lambda x: x['score'], reverse=True)
    
    # Merge overlapping/close highlights
    merged = []
    for h in highlights:
        if not merged:
            merged.append(h)
        else:
            last = merged[-1]
            # If this highlight starts within 5s of last one ending, merge them
            if h['start'] - last['end'] < 5:
                last['end'] = h['end']
                last['score'] = max(last['score'], h['score'])
                last['text'] += " | " + h['text']
            else:
                merged.append(h)
    
    log(f"✓ Found {len(merged)} highlight moments")
    return merged


def create_clips(video_path, highlights, settings, num_clips=3, transcription=None, video_info=None):
    """Create short-form clips from highlights with Phase 2 effects."""
    log(f"\n✂️  Creating {num_clips} clips with advanced effects...")
    
    # Create output directory
    video_name = Path(video_path).stem
    output_dir = os.path.join(HERE, "Output", video_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Import Phase 2 tools
    try:
        from tools import (
            generate_caption_burns,
            generate_srt_file,
            detect_zoom_moments,
            calculate_speed_map,
            create_speed_filter,
            detect_silence_segments
        )
        phase2_available = True
        log("   ✓ Phase 2 features loaded")
    except ImportError as e:
        log(f"   ⚠️  Phase 2 features not available: {e}")
        log("   Falling back to basic mode")
        phase2_available = False
    
    # Select top N highlights
    selected = highlights[:num_clips]
    
    clips_created = []
    target_duration = settings['clip_selection']['target_duration_s']
    
    # Generate SRT captions if transcription available
    if transcription and phase2_available:
        metadata_dir = os.path.join(output_dir, "_metadata")
        os.makedirs(metadata_dir, exist_ok=True)
        srt_file = generate_srt_file(transcription, metadata_dir)
        if srt_file:
            log(f"   ✓ Generated SRT captions: {os.path.basename(srt_file)}")
    
    # Detect zoom moments
    zoom_moments = []
    if phase2_available and settings['zoom'].get('enabled', False):
        zoom_moments = detect_zoom_moments(transcription, settings)
        if zoom_moments:
            log(f"   ✓ Detected {len(zoom_moments)} zoom moments")
    
    # Process each clip
    for i, highlight in enumerate(selected, 1):
        log(f"\n   Clip {i}/{num_clips}: {highlight['start']:.1f}s - {highlight['end']:.1f}s")
        log(f"   Text: {highlight['text'][:60]}...")
        
        # Calculate clip duration and adjust if needed
        duration = highlight['end'] - highlight['start']
        if duration > settings['clip_selection']['max_duration_s']:
            # Trim to max duration, centered on original
            excess = duration - target_duration
            highlight['start'] += excess / 2
            highlight['end'] -= excess / 2
            duration = target_duration
        
        # Output filename
        output_file = os.path.join(output_dir, f"clip_{i:03d}_{video_name}.mp4")
        
        # Generate caption filter for this clip
        caption_filter = None
        if phase2_available and settings['captions'].get('enabled', False) and transcription:
            # Get transcription segment for this clip
            clip_transcription = get_clip_transcription(transcription, highlight['start'], highlight['end'])
            if clip_transcription:
                caption_filter = generate_caption_burns(clip_transcription, settings, output_dir)
                if caption_filter:
                    log("      ✓ Captions enabled")
        
        # Calculate speed filter for this clip
        speed_filter = None
        if phase2_available and settings['speed'].get('enabled', False) and transcription:
            clip_transcription = get_clip_transcription(transcription, highlight['start'], highlight['end'])
            if clip_transcription:
                speed_map = calculate_speed_map(clip_transcription, [], settings)
                speed_filter = create_speed_filter(speed_map, duration)
                if speed_filter:
                    log(f"      ✓ Speed ramping: avg {speed_filter.get('average_speed', 1.0):.2f}x")
        
        # Get zoom moments for this clip
        clip_zooms = [zm for zm in zoom_moments 
                     if highlight['start'] <= zm['time'] <= highlight['end']]
        
        # Create clip using advanced processor
        if phase2_available:
            from tools import process_clip_advanced
            success = process_clip_advanced(
                video_path,
                highlight['start'],
                highlight['end'],
                output_file,
                settings,
                transcription_segment=clip_transcription if 'clip_transcription' in locals() else None,
                caption_filter=caption_filter,
                speed_filter=speed_filter,
                zoom_filter=clip_zooms if clip_zooms else None
            )
        else:
            # Fallback to basic extraction
            success = extract_clip_ffmpeg(
                video_path,
                highlight['start'],
                highlight['end'],
                output_file,
                settings
            )
        
        if success:
            log(f"   ✓ Created: {os.path.basename(output_file)}")
            clips_created.append({
                'file': output_file,
                'start': highlight['start'],
                'end': highlight['end'],
                'duration': duration,
                'text': highlight['text'],
                'score': highlight['score'],
                'has_captions': caption_filter is not None,
                'has_speed_ramping': speed_filter is not None,
                'zoom_moments': len(clip_zooms) if clip_zooms else 0
            })
        else:
            log(f"   ✗ Failed to create clip {i}")
    
    # Save metadata
    metadata_dir = os.path.join(output_dir, "_metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    
    metadata = {
        'source_video': video_path,
        'clips': clips_created,
        'settings': settings,
        'phase2_enabled': phase2_available
    }
    
    metadata_file = os.path.join(metadata_dir, "clips_metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    log(f"\n✅ Created {len(clips_created)} clips in: {output_dir}")
    return clips_created


def save_timestamps_for_capcut(video_path, highlights, transcription):
    """Save timestamp file for manual CapCut editing."""
    video_name = Path(video_path).stem
    output_dir = os.path.join(HERE, "Output", video_name)
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp_file = os.path.join(output_dir, "CAPCUT_TIMESTAMPS.txt")
    
    with open(timestamp_file, 'w', encoding='utf-8') as f:
        f.write(f"# CapCut Timestamps for: {os.path.basename(video_path)}\n")
        f.write(f"# Import your video into CapCut, then cut at these times:\n\n")
        f.write("=" * 80 + "\n\n")
        
        for i, highlight in enumerate(highlights, 1):
            start_min = int(highlight['start'] // 60)
            start_sec = highlight['start'] % 60
            end_min = int(highlight['end'] // 60)
            end_sec = highlight['end'] % 60
            duration = highlight['end'] - highlight['start']
            
            f.write(f"CLIP {i}\n")
            f.write(f"  Start:    {start_min}:{start_sec:05.2f}  ({highlight['start']:.2f}s)\n")
            f.write(f"  End:      {end_min}:{end_sec:05.2f}  ({highlight['end']:.2f}s)\n")
            f.write(f"  Duration: {duration:.1f} seconds\n")
            f.write(f"  Content:  {highlight['text'][:70]}\n")
            f.write(f"  Score:    {highlight['score']:.2f}\n")
            f.write("\n" + "-" * 80 + "\n\n")
        
        f.write("\n\nINSTRUCTIONS FOR CAPCUT:\n")
        f.write("1. Import your full video into CapCut\n")
        f.write("2. For each clip above:\n")
        f.write("   a. Find the Start timestamp on timeline\n")
        f.write("   b. Split the video there\n")
        f.write("   c. Find the End timestamp\n")
        f.write("   d. Split again\n")
        f.write("   e. Delete everything except that segment\n")
        f.write("3. Crop to 9:16 vertical (1080x1920)\n")
        f.write("4. Add captions using CapCut's auto-captions\n")
        f.write("5. Add zoom/effects on reaction moments\n")
        f.write("6. Export and post!\n")
    
    log(f"\n✓ Timestamps saved to: {timestamp_file}")
    log(f"  Found {len(highlights)} clips to edit in CapCut")
    
    return timestamp_file


def get_clip_transcription(transcription, start_time, end_time):
    """Extract transcription segments for a specific time range."""
    if not transcription or 'segments' not in transcription:
        return None
    
    clip_segments = []
    for segment in transcription['segments']:
        # Check if segment overlaps with clip time range
        if segment['start'] <= end_time and segment['end'] >= start_time:
            # Adjust segment times relative to clip start
            adjusted_segment = segment.copy()
            adjusted_segment['start'] = max(0, segment['start'] - start_time)
            adjusted_segment['end'] = min(end_time - start_time, segment['end'] - start_time)
            
            # Adjust word timings if available
            if 'words' in adjusted_segment:
                adjusted_words = []
                for word in adjusted_segment['words']:
                    if start_time <= word['start'] <= end_time:
                        adjusted_word = word.copy()
                        adjusted_word['start'] = word['start'] - start_time
                        adjusted_word['end'] = word['end'] - start_time
                        adjusted_words.append(adjusted_word)
                adjusted_segment['words'] = adjusted_words
            
            clip_segments.append(adjusted_segment)
    
    return {'segments': clip_segments} if clip_segments else None


def extract_clip_ffmpeg(input_video, start_time, end_time, output_file, settings):
    """Extract clip using FFmpeg with vertical crop (basic fallback)."""
    
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-ss", str(start_time),  # Start time
        "-i", input_video,  # Input file
        "-t", str(end_time - start_time),  # Duration
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",  # Vertical crop
        "-c:v", "libx264",  # Video codec
        "-preset", "medium",  # Encoding speed
        "-crf", "23",  # Quality (lower = better)
        "-c:a", "aac",  # Audio codec
        "-b:a", "192k",  # Audio bitrate
        "-ar", "48000",  # Audio sample rate
        output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per clip
        )
        return result.returncode == 0
    except Exception as e:
        log(f"      FFmpeg error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert long videos into viral short clips")
    parser.add_argument("video", nargs="?", help="Path to input video file")
    parser.add_argument("--clips", type=int, default=3, help="Number of clips to generate (default: 3)")
    parser.add_argument("--duration", type=int, default=45, help="Target clip duration in seconds (default: 45)")
    parser.add_argument("--style", choices=["viral", "clean", "minimal"], default="viral", help="Caption style")
    parser.add_argument("--check-deps", action="store_true", help="Check if dependencies are installed")
    parser.add_argument("--batch", help="Process multiple videos (glob pattern)")
    parser.add_argument("--timestamps-only", action="store_true", help="Only generate timestamps file (no clip extraction)")
    
    args = parser.parse_args()
    
    log("=" * 80)
    log("AutoEditShortForm - Viral Short Clip Generator")
    log("=" * 80)
    
    # Check dependencies
    if args.check_deps or not args.video:
        if not check_dependencies():
            log("\n❌ Please install missing dependencies first")
            sys.exit(1)
        else:
            log("\n✅ All dependencies installed!")
            if not args.video:
                return
    
    # Get video file(s)
    if args.batch:
        videos = glob.glob(args.batch)
        if not videos:
            log(f"❌ No videos found matching: {args.batch}")
            sys.exit(1)
    else:
        if not args.video:
            log("\n❌ Please provide a video file")
            log("   Usage: python autoshort.py \"video.mp4\"")
            sys.exit(1)
        videos = [args.video]
    
    # Load settings
    settings = load_settings()
    settings['clip_selection']['target_duration_s'] = args.duration
    settings['captions']['style'] = args.style
    
    # Process each video
    for video_path in videos:
        video_path = os.path.abspath(video_path)
        
        if not os.path.exists(video_path):
            log(f"\n❌ Video not found: {video_path}")
            continue
        
        log(f"\n📹 Processing: {os.path.basename(video_path)}")
        
        # Get video info
        video_info = get_video_info(video_path)
        log(f"   Resolution: {video_info['width']}x{video_info['height']}")
        log(f"   Duration: {video_info['duration']:.1f}s ({video_info['duration']/60:.1f} min)")
        
        # Transcribe
        transcription = transcribe_video(video_path, model_size="base")
        if not transcription:
            log("❌ Transcription failed, skipping video")
            continue
        
        # Find highlights
        highlights = find_highlights(transcription, video_info, settings)
        if not highlights:
            log("❌ No highlights found, try a different video")
            continue
        
        # If timestamps-only mode, just save timestamps and exit
        if args.timestamps_only:
            save_timestamps_for_capcut(video_path, highlights[:args.clips], transcription)
            log(f"\n✅ Timestamps saved! Import video into CapCut and use the timestamps file.")
            continue
        
        # Create clips with Phase 2 features
        clips = create_clips(video_path, highlights, settings, args.clips, transcription, video_info)
        
        if clips:
            log(f"\n✅ SUCCESS! {len(clips)} clips ready:")
            for clip in clips:
                log(f"   • {os.path.basename(clip['file'])} ({clip['duration']:.1f}s)")
        else:
            log("\n❌ No clips created")
    
    log("\n" + "=" * 80)
    log("DONE! Check the Output/ folder for your clips")
    log("=" * 80)


if __name__ == "__main__":
    main()
