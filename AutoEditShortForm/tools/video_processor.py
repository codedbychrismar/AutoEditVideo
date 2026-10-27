"""Video Processor - Advanced FFmpeg operations with all effects combined."""

import subprocess
import os
from typing import Dict, List, Optional


def process_clip_advanced(
    input_video,
    start_time,
    end_time,
    output_file,
    settings,
    transcription_segment=None,
    caption_filter=None,
    speed_filter=None,
    zoom_filter=None
):
    """
    Extract and process clip with all advanced effects:
    - Vertical crop (9:16)
    - Captions (word-by-word animated)
    - Speed ramping
    - Zoom effects
    - High quality output
    """
    
    duration = end_time - start_time
    
    # Build complex filter chain
    filter_parts = []
    
    # 1. Crop to vertical 9:16
    crop_cfg = settings['crop']
    width = crop_cfg['width']
    height = crop_cfg['height']
    
    # Scale and crop to vertical format
    # Force original aspect ratio, then crop to exact 9:16
    crop_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
    filter_parts.append(crop_filter)
    
    # 2. Apply zoom effects if enabled
    if zoom_filter and settings['zoom'].get('enabled', False):
        # Simplified zoom - just apply slight scale
        # Full implementation would have dynamic zooming
        filter_parts.append("scale=iw*1.05:ih*1.05")
    
    # 3. Apply speed ramping if enabled
    # Note: Speed ramping is applied separately to video and audio
    video_speed = None
    audio_speed = None
    
    if speed_filter and settings['speed'].get('enabled', False):
        video_speed = speed_filter.get('video')
        audio_speed = speed_filter.get('audio')
        if video_speed:
            filter_parts.append(video_speed)
    
    # 4. Apply captions if enabled
    if caption_filter and settings['captions'].get('enabled', False):
        # Add caption burns (drawtext filters)
        filter_parts.append(caption_filter)
    
    # Combine all video filters
    video_filter_complex = ','.join(filter_parts) if filter_parts else None
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-ss', str(start_time),  # Start time
        '-i', input_video,  # Input file
        '-t', str(duration),  # Duration
    ]
    
    # Add video filters
    if video_filter_complex:
        cmd.extend(['-vf', video_filter_complex])
    
    # Add audio filters (speed)
    if audio_speed:
        cmd.extend(['-af', audio_speed])
    
    # Output settings
    output_cfg = settings['output']
    cmd.extend([
        '-c:v', 'libx264',  # Video codec
        '-preset', 'medium',  # Encoding speed
        '-crf', '23' if output_cfg['quality'] == 'high' else '20',  # Quality
        '-c:a', 'aac',  # Audio codec
        '-b:a', output_cfg.get('audio_bitrate', '192k'),
        '-ar', output_cfg.get('audio_sample_rate', '48000'),
        '-r', str(output_cfg.get('fps', 30)),  # Frame rate
        output_file
    ])
    
    # Execute FFmpeg
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr[:500]}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("FFmpeg timeout - clip too long or system too slow")
        return False
    except Exception as e:
        print(f"Error processing clip: {e}")
        return False


def add_background_music(video_path, music_path, output_path, music_volume=0.3):
    """
    Add background music to video (optional feature).
    
    Args:
        video_path: Input video
        music_path: Background music file
        output_path: Output video
        music_volume: Music volume (0.0 to 1.0)
    """
    cmd = [
        'ffmpeg',
        '-y',
        '-i', video_path,
        '-i', music_path,
        '-filter_complex',
        f'[1:a]volume={music_volume}[a1];[0:a][a1]amix=inputs=2:duration=first[aout]',
        '-map', '0:v',
        '-map', '[aout]',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=300)
        return True
    except Exception as e:
        print(f"Could not add background music: {e}")
        return False


def create_compilation(clip_paths, output_path, settings):
    """
    Combine multiple clips into one compilation video.
    
    Args:
        clip_paths: List of video file paths
        output_path: Output compilation video
        settings: Settings dict
    """
    if len(clip_paths) < 2:
        return False
    
    # Create concat file
    concat_file = output_path.replace('.mp4', '_concat.txt')
    with open(concat_file, 'w') as f:
        for clip in clip_paths:
            f.write(f"file '{os.path.abspath(clip)}'\n")
    
    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c', 'copy',
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=300)
        os.remove(concat_file)
        return True
    except Exception as e:
        print(f"Could not create compilation: {e}")
        return False


def extract_thumbnail(video_path, output_path, timestamp=None):
    """
    Extract a thumbnail image from video.
    
    Args:
        video_path: Input video
        output_path: Output image path (jpg/png)
        timestamp: Time in seconds (None = middle of video)
    """
    if timestamp is None:
        # Get video duration and use middle frame
        import json
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        duration = float(info['format']['duration'])
        timestamp = duration / 2
    
    cmd = [
        'ffmpeg',
        '-y',
        '-ss', str(timestamp),
        '-i', video_path,
        '-frames:v', '1',
        '-q:v', '2',
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=30)
        return True
    except Exception as e:
        print(f"Could not extract thumbnail: {e}")
        return False
