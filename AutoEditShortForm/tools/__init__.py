"""Tools package for AutoEditShortForm advanced features."""

from .audio_analyzer import (
    detect_silence_segments,
    analyze_audio_energy,
    calculate_speed_map,
    create_speed_filter
)

from .caption_generator import (
    generate_caption_burns,
    generate_srt_file,
    create_caption_style_preset
)

from .zoom_effects import (
    detect_zoom_moments,
    create_zoom_filter,
    get_zoom_positions
)

from .video_processor import (
    process_clip_advanced,
    add_background_music,
    create_compilation,
    extract_thumbnail
)

__all__ = [
    'detect_silence_segments',
    'analyze_audio_energy',
    'calculate_speed_map',
    'create_speed_filter',
    'generate_caption_burns',
    'generate_srt_file',
    'create_caption_style_preset',
    'detect_zoom_moments',
    'create_zoom_filter',
    'get_zoom_positions',
    'process_clip_advanced',
    'add_background_music',
    'create_compilation',
    'extract_thumbnail'
]
