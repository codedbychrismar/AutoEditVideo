"""Caption Generator - Creates animated word-by-word captions in viral TikTok style."""

import json
import os
from typing import List, Dict, Tuple


def generate_caption_burns(transcription, settings, output_path):
    """
    Generate FFmpeg drawtext filters for word-by-word animated captions.
    
    Returns: FFmpeg filter string for burning captions into video
    """
    if not transcription or 'segments' not in transcription:
        return None
    
    caption_cfg = settings['captions']
    
    # Extract all words with timestamps
    words = []
    for segment in transcription['segments']:
        if 'words' in segment:
            for word in segment['words']:
                words.append({
                    'text': word['word'].strip(),
                    'start': word['start'],
                    'end': word['end']
                })
    
    if not words:
        return None
    
    # Build FFmpeg drawtext filter chain
    filters = []
    
    # Font settings
    font_file = caption_cfg.get('font', 'Arial-Bold')
    font_size = caption_cfg.get('font_size', 72)
    text_color = caption_cfg['color'].replace('#', '0x')
    outline_color = caption_cfg['outline_color'].replace('#', '0x')
    outline_width = caption_cfg['outline_width']
    
    # Position settings
    position = caption_cfg.get('position', 'center')
    if position == 'center':
        x_pos = '(w-text_w)/2'
        y_pos = '(h-text_h)/2'
    elif position == 'bottom':
        x_pos = '(w-text_w)/2'
        y_pos = 'h-text_h-100'
    else:  # top
        x_pos = '(w-text_w)/2'
        y_pos = '100'
    
    # Group words (3 words at a time for readability)
    words_per_caption = caption_cfg.get('words_per_caption', 3)
    
    grouped = []
    for i in range(0, len(words), words_per_caption):
        group = words[i:i + words_per_caption]
        text = ' '.join([w['text'] for w in group])
        start = group[0]['start']
        end = group[-1]['end']
        grouped.append({
            'text': text.upper() if caption_cfg.get('uppercase', False) else text,
            'start': start,
            'end': end
        })
    
    # Create drawtext filter for each caption with enable expression
    for i, caption in enumerate(grouped):
        # Escape text for FFmpeg
        text = caption['text'].replace("'", "'\\\\\\''").replace(":", "\\:")
        
        # Enable expression: show only during this caption's time window
        enable_expr = f"between(t,{caption['start']:.3f},{caption['end']:.3f})"
        
        # Animation: scale in effect (pop animation)
        if caption_cfg.get('animation') == 'pop':
            # Calculate progress in animation (0 to 1)
            anim_duration = 0.15  # 150ms animation
            # Scale from 0.8 to 1.0 over animation duration
            scale_expr = f"if(lt(t-{caption['start']},{anim_duration}),0.8+0.2*(t-{caption['start']})/{anim_duration},1.0)"
            font_size_expr = f"{font_size}*{scale_expr}"
        else:
            font_size_expr = str(font_size)
        
        filter_text = (
            f"drawtext="
            f"text='{text}':"
            f"fontfile='{font_file}':"
            f"fontsize={font_size_expr}:"
            f"fontcolor={text_color}:"
            f"borderw={outline_width}:"
            f"bordercolor={outline_color}:"
            f"x={x_pos}:"
            f"y={y_pos}:"
            f"enable='{enable_expr}'"
        )
        
        filters.append(filter_text)
    
    # Join all filters with comma
    filter_complex = ','.join(filters)
    
    return filter_complex


def generate_srt_file(transcription, output_path):
    """Generate SRT subtitle file from transcription."""
    if not transcription or 'segments' not in transcription:
        return None
    
    srt_lines = []
    
    for i, segment in enumerate(transcription['segments'], 1):
        start_time = format_srt_time(segment['start'])
        end_time = format_srt_time(segment['end'])
        text = segment['text'].strip()
        
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")  # Blank line between entries
    
    srt_content = '\n'.join(srt_lines)
    
    srt_path = os.path.join(output_path, "captions.srt")
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    return srt_path


def format_srt_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def create_caption_style_preset(style_name):
    """Return preset caption styles."""
    presets = {
        'viral': {
            'font': 'Arial-Bold',
            'font_size': 80,
            'color': '#FFD700',  # Gold yellow
            'outline_color': '#000000',
            'outline_width': 6,
            'animation': 'pop',
            'words_per_caption': 3,
            'position': 'center',
            'uppercase': True
        },
        'clean': {
            'font': 'Arial',
            'font_size': 60,
            'color': '#FFFFFF',
            'outline_color': '#000000',
            'outline_width': 3,
            'animation': 'fade',
            'words_per_caption': 5,
            'position': 'bottom',
            'uppercase': False
        },
        'minimal': {
            'font': 'Arial',
            'font_size': 48,
            'color': '#FFFFFF',
            'outline_color': '#000000',
            'outline_width': 2,
            'animation': 'none',
            'words_per_caption': 7,
            'position': 'bottom',
            'uppercase': False
        }
    }
    
    return presets.get(style_name, presets['viral'])
