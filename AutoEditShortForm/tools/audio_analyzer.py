"""Audio Analyzer - Detect silence, energy levels, and optimal speed segments."""

import subprocess
import json
import re
from typing import List, Dict, Tuple


def detect_silence_segments(video_path, threshold_db=-40, min_duration_ms=500):
    """
    Detect silent segments in video using FFmpeg silencedetect filter.
    
    Returns list of silence periods: [{'start': 1.5, 'end': 2.3, 'duration': 0.8}, ...]
    """
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-af', f'silencedetect=noise={threshold_db}dB:d={min_duration_ms/1000}',
        '-f', 'null',
        '-'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Parse FFmpeg output for silence periods
        output = result.stderr
        
        silence_starts = []
        silence_ends = []
        
        # Find all silence_start and silence_end
        for line in output.split('\n'):
            if 'silence_start' in line:
                match = re.search(r'silence_start: ([\d.]+)', line)
                if match:
                    silence_starts.append(float(match.group(1)))
            
            if 'silence_end' in line:
                match = re.search(r'silence_end: ([\d.]+)', line)
                if match:
                    silence_ends.append(float(match.group(1)))
        
        # Pair starts and ends
        silences = []
        for i in range(min(len(silence_starts), len(silence_ends))):
            silences.append({
                'start': silence_starts[i],
                'end': silence_ends[i],
                'duration': silence_ends[i] - silence_starts[i]
            })
        
        return silences
        
    except Exception as e:
        print(f"Warning: Could not detect silence: {e}")
        return []


def analyze_audio_energy(video_path):
    """
    Analyze audio energy levels throughout video.
    
    Returns list of energy segments with timestamps and energy levels.
    """
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-af', 'astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-',
        '-f', 'null',
        '-'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Parse energy levels (simplified - in real implementation would need more parsing)
        # For now, return empty - this is a placeholder for advanced feature
        return []
        
    except Exception as e:
        print(f"Warning: Could not analyze audio energy: {e}")
        return []


def calculate_speed_map(transcription, silences, settings):
    """
    Create a speed map for the video based on speech and silence.
    
    Returns list of segments with speed multipliers:
    [{'start': 0, 'end': 5.2, 'speed': 1.0}, {'start': 5.2, 'end': 7.1, 'speed': 2.0}, ...]
    """
    if not transcription or 'segments' not in transcription:
        return [{'start': 0, 'end': 999999, 'speed': 1.0}]
    
    speed_cfg = settings.get('speed', {})
    normal_speed = speed_cfg.get('normal', 1.0)
    fast_speed = speed_cfg.get('fast', 1.75)
    slow_speed = speed_cfg.get('slow', 0.65)
    silence_speed = speed_cfg.get('silence_speed', 2.0)
    
    segments = []
    
    # Create speech segments (normal or slow speed)
    for seg in transcription['segments']:
        text = seg['text'].lower()
        
        # Detect if this is a highlight moment (should be slowed down)
        is_highlight = any(keyword in text for keyword in [
            'oh my god', "let's go", 'what the', 'no way', 'insane', 
            'crazy', 'holy', 'wow', 'sick'
        ])
        
        speed = slow_speed if is_highlight else normal_speed
        
        segments.append({
            'start': seg['start'],
            'end': seg['end'],
            'speed': speed,
            'type': 'highlight' if is_highlight else 'speech'
        })
    
    # Fill gaps (silence) with fast speed
    all_times = sorted(set([0] + [s['start'] for s in segments] + [s['end'] for s in segments]))
    
    filled_segments = []
    for i in range(len(all_times) - 1):
        start = all_times[i]
        end = all_times[i + 1]
        
        # Check if this time range is covered by a speech segment
        covered = any(
            s['start'] <= start and s['end'] >= end 
            for s in segments
        )
        
        if covered:
            # Find the matching segment
            for s in segments:
                if s['start'] <= start and s['end'] >= end:
                    filled_segments.append({
                        'start': start,
                        'end': end,
                        'speed': s['speed'],
                        'type': s['type']
                    })
                    break
        else:
            # This is a gap (silence) - speed it up
            # But only if it's long enough (> 0.5s)
            if end - start > 0.5:
                filled_segments.append({
                    'start': start,
                    'end': end,
                    'speed': silence_speed,
                    'type': 'silence'
                })
            else:
                # Too short to bother speeding up
                filled_segments.append({
                    'start': start,
                    'end': end,
                    'speed': normal_speed,
                    'type': 'transition'
                })
    
    return filled_segments


def create_speed_filter(speed_map, video_duration):
    """
    Create FFmpeg setpts/atempo filter chain for variable speed.
    
    This is complex - returns simplified version for now.
    Full implementation would require video segmentation and concatenation.
    """
    # For Phase 2, we'll use a simplified approach:
    # Apply average speed to entire clip
    
    avg_speed = sum(s['speed'] for s in speed_map) / len(speed_map) if speed_map else 1.0
    
    # Clamp to reasonable range
    avg_speed = max(0.5, min(2.0, avg_speed))
    
    if abs(avg_speed - 1.0) < 0.05:
        return None  # No speed change needed
    
    # Video speed filter
    video_filter = f"setpts={1/avg_speed}*PTS"
    
    # Audio speed filter (atempo only works in range 0.5-2.0)
    if 0.5 <= avg_speed <= 2.0:
        audio_filter = f"atempo={avg_speed}"
    else:
        # Chain multiple atempo filters for extreme speeds
        audio_filter = "atempo=2.0" if avg_speed > 2.0 else "atempo=0.5"
    
    return {
        'video': video_filter,
        'audio': audio_filter,
        'average_speed': avg_speed
    }


def remove_silence_segments(video_path, output_path, silences, buffer_ms=100):
    """
    Remove silence segments from video (advanced - requires segment cutting).
    
    For Phase 2: Returns filter for simple silence removal.
    Full implementation would cut and concatenate segments.
    """
    if not silences:
        return None
    
    # Simple approach: use FFmpeg's silenceremove filter
    # This is a real-time filter that's less precise but easier
    
    filter_str = f"silenceremove=start_periods=1:stop_periods=-1:start_threshold=-50dB:stop_threshold=-50dB:start_silence={buffer_ms/1000}:stop_silence={buffer_ms/1000}"
    
    return filter_str
