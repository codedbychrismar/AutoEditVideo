"""Zoom Effects - Add dynamic zoom punches on highlight moments."""

from typing import List, Dict


def detect_zoom_moments(transcription, settings):
    """
    Detect moments that should have zoom effects.
    
    Returns list of zoom triggers: [{'time': 5.2, 'duration': 0.3, 'amount': 1.15}, ...]
    """
    if not transcription or 'segments' not in transcription:
        return []
    
    zoom_cfg = settings.get('zoom', {})
    if not zoom_cfg.get('enabled', False):
        return []
    
    zoom_amount = zoom_cfg.get('amount', 1.15)
    duration_frames = zoom_cfg.get('duration_frames', 10)
    fps = settings['output'].get('fps', 30)
    duration_seconds = duration_frames / fps
    
    # Keywords that trigger zoom
    zoom_keywords = [
        'oh my god', "let's go", 'what the', 'no way',
        'insane', 'crazy', 'holy', 'wow', 'sick',
        'killed', 'dead', 'clutch', 'gg'
    ]
    
    zoom_moments = []
    
    for segment in transcription['segments']:
        text = segment['text'].lower()
        
        # Check if segment contains zoom-worthy keywords
        for keyword in zoom_keywords:
            if keyword in text:
                # Find word-level timing if available
                if 'words' in segment:
                    for word in segment['words']:
                        if keyword in word['word'].lower():
                            zoom_moments.append({
                                'time': word['start'],
                                'duration': duration_seconds,
                                'amount': zoom_amount,
                                'keyword': keyword
                            })
                            break
                else:
                    # Use segment start if word-level timing not available
                    zoom_moments.append({
                        'time': segment['start'],
                        'duration': duration_seconds,
                        'amount': zoom_amount,
                        'keyword': keyword
                    })
                break  # Only one zoom per segment
    
    return zoom_moments


def create_zoom_filter(zoom_moments, video_duration, settings):
    """
    Create FFmpeg zoompan filter for dynamic zoom effects.
    
    Returns FFmpeg filter string.
    """
    if not zoom_moments:
        return None
    
    zoom_cfg = settings.get('zoom', {})
    smooth = zoom_cfg.get('smooth', True)
    fps = settings['output'].get('fps', 30)
    
    # Build zoompan filter with multiple zoom moments
    # This is a simplified version - full implementation would be more complex
    
    # For now, we'll create a more basic approach:
    # Apply slight zoom to entire video with pulses at zoom moments
    
    # Simple approach: use scale filter with expression
    base_zoom = 1.0
    
    # Build conditional zoom expression
    # Format: if(between(t,start,end), zoom_value, base_zoom)
    
    zoom_expr = str(base_zoom)
    
    for zm in zoom_moments:
        start = zm['time']
        end = zm['time'] + zm['duration']
        amount = zm['amount']
        
        # Add this zoom moment to the expression
        # Use smooth transition with sine wave
        if smooth:
            # Sine wave for smooth in/out
            progress_expr = f"(t-{start})/{zm['duration']}"
            sine_expr = f"sin({progress_expr}*PI)"
            zoom_value = f"{base_zoom}+({amount}-{base_zoom})*{sine_expr}"
        else:
            # Instant zoom
            zoom_value = str(amount)
        
        # Wrap in if condition
        zoom_expr = f"if(between(t,{start},{end}),{zoom_value},{zoom_expr})"
    
    # Apply zoom using scale filter
    # Note: This is a simplified approach. Real implementation might need zoompan
    filter_str = f"scale=iw*{zoom_expr}:ih*{zoom_expr}"
    
    return filter_str


def create_simple_zoom_filter(zoom_amount=1.15):
    """Create a simple static zoom filter (fallback)."""
    return f"scale=iw*{zoom_amount}:ih*{zoom_amount},crop=iw/{zoom_amount}:ih/{zoom_amount}"


def get_zoom_positions(video_info, zoom_moments):
    """
    Calculate zoom center positions (for face/action tracking).
    
    For Phase 2: Returns center position. Phase 3 will add face tracking.
    """
    positions = []
    
    for zm in zoom_moments:
        positions.append({
            'time': zm['time'],
            'x': 0.5,  # Center X (0-1 normalized)
            'y': 0.5,  # Center Y (0-1 normalized)
            'amount': zm['amount']
        })
    
    return positions
