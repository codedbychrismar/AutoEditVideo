r"""AutoGenerate - Creates missing content (script, images, voice) from an idea.

    python autogenerate.py "<content folder>" --idea "your video idea"
    
If Pictures, Voice, or guide already exist, they are kept. Only missing parts are generated.
"""
import argparse, json, os, sys, time, glob, re

HERE = os.path.dirname(os.path.abspath(__file__))
YTA = os.path.dirname(HERE)


def log(*a):
    print(*a, flush=True)


def check_existing_content(folder):
    """Check what content already exists."""
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    
    status = {
        "has_images": False,
        "has_voice": False,
        "has_guide": False,
        "images_count": 0,
        "voice_count": 0,
        "guide_path": None
    }
    
    # Check for Pictures folder
    for subdir in ["Pictures", "Picture", "Images", "Image"]:
        pic_path = os.path.join(folder, subdir)
        if os.path.isdir(pic_path):
            images = [f for f in os.listdir(pic_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if images:
                status["has_images"] = True
                status["images_count"] = len(images)
                log(f"✓ Found {len(images)} images in {subdir}/")
                break
    
    # Check for Voice folder
    for subdir in ["Voice", "Voices", "VO", "Audio"]:
        voice_path = os.path.join(folder, subdir)
        if os.path.isdir(voice_path):
            voices = [f for f in os.listdir(voice_path) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
            if voices:
                status["has_voice"] = True
                status["voice_count"] = len(voices)
                log(f"✓ Found {len(voices)} voice files in {subdir}/")
                break
    
    # Check for guide markdown
    guides = [g for g in glob.glob(os.path.join(folder, "*.md"))
              if re.search(r'beat\s+\d+', open(g, encoding='utf-8', errors='ignore').read(), re.I)]
    if guides:
        status["has_guide"] = True
        status["guide_path"] = guides[0]
        log(f"✓ Found guide: {os.path.basename(guides[0])}")
    
    return status


def generate_script_and_guide(idea, folder, target_length_min=8):
    """Generate script and guide markdown from idea using AI."""
    log(f"\n🤖 Generating script and guide for: {idea}")
    log(f"   Target length: {target_length_min} minutes (~{target_length_min * 150} words)")
    
    word_count = target_length_min * 150  # ~2.5 words per second
    beat_count = int(word_count / 10)  # ~10 words per beat
    
    # Create guide template (works without API keys)
    log("📝 Creating guide template...")
    
    guide_content = f"""# VIDEO SCRIPT AND GUIDE
## "{idea}"

**Target length:** {target_length_min} minutes (~{word_count} words)
**Beats needed:** ~{beat_count}

---

## SECTION 1: HOOK (Beats 1-5)

### Beat 1 — 0:00-0:05
**Script Segment:** "[Opening hook - grab attention immediately]"

**Full Image Prompt:** [Describe the opening image in detail - characters, setting, mood, colors]

- **Camera Angle:** [Wide/Medium/Close, eye level/high/low]
- **Lighting:** [Warm/Cool, bright/dim, time of day]
- **Mood:** [Tense/Curious/Exciting/etc]
- **Action:** [What's happening in the scene]
- **Color Palette:** [Primary colors to use]

### Beat 2 — 0:05-0:10
**Script Segment:** "[Continue the hook - build curiosity]"

**Full Image Prompt:** [Next image description]

- **Camera Angle:** [...]
- **Lighting:** [...]
- **Mood:** [...]
- **Action:** [...]
- **Color Palette:** [...]

[... Continue for ~{beat_count} beats total ...]

---

## INSTRUCTIONS FOR COMPLETION:

1. Write the full script in the "Script Segment" lines
2. Describe each image in the "Full Image Prompt" sections
3. Aim for {beat_count} beats total (for {target_length_min} min video)
4. Each beat should be 5-10 seconds of narration (~10-25 words)
5. Include clear visual descriptions for every beat

## TIPS:

- Start with a strong hook (beats 1-5)
- Build curiosity in the setup (beats 6-15)
- Deliver the main content (beats 16-{beat_count-15})
- End with a satisfying conclusion (last 5-10 beats)
- Each image needs enough detail to generate consistently

## ONCE COMPLETE:

Run this command to extract image prompts:
  python autogenerate.py "{folder}"

Then:
1. Generate images from the extracted prompts (Midjourney/DALL-E)
2. Create voice files (record or use TTS)
3. Run AutoEditLongForm to create the timeline
"""
    
    # Clean filename - remove invalid characters
    safe_name = idea.lower().replace(' ', '_').replace('?', '').replace('!', '').replace(':', '').replace('"', '').replace("'", '')
    guide_path = os.path.join(folder, f"{safe_name}_guide.md")
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    log(f"✓ Created guide template: {os.path.basename(guide_path)}")
    log(f"\n📝 NEXT STEPS:")
    log(f"   1. Open: {guide_path}")
    log(f"   2. Write your script in each 'Script Segment' line")
    log(f"   3. Describe images in each 'Full Image Prompt' section")
    log(f"   4. Run autogenerate again to create voice and images")
    
    return guide_path


def generate_voice_from_guide(guide_path, folder):
    """Generate voice files from script using TTS."""
    log(f"\n🎙️ Generating voice from guide...")
    
    # Check for TTS capability
    try:
        import openai
        has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    except ImportError:
        has_openai = False
    
    if not has_openai:
        log("⚠️  Voice generation requires:")
        log("   - pip install openai")
        log("   - Set OPENAI_API_KEY environment variable")
        log("   For now, you'll need to create voice files manually")
        return False
    
    # Extract script from guide
    with open(guide_path, 'r', encoding='utf-8') as f:
        guide_text = f.read()
    
    # Find all script segments
    script_pattern = r'\*\*Script Segment:\*\*\s*["\']?([^"\'\n]+)["\']?'
    segments = re.findall(script_pattern, guide_text, re.IGNORECASE)
    
    if not segments or all(seg.startswith('[') for seg in segments):
        log("⚠️  No completed script found in guide (still has placeholders)")
        log("   Fill in the 'Script Segment' lines first")
        return False
    
    log(f"   Found {len(segments)} script segments")
    
    # TODO: Implement TTS generation
    log("⚠️  TTS generation not yet implemented")
    log("   Voice files should be created manually for now")
    
    return False


def generate_image_prompts(guide_path, folder):
    """Extract image prompts from guide for manual generation."""
    log(f"\n🖼️  Extracting image prompts from guide...")
    
    with open(guide_path, 'r', encoding='utf-8') as f:
        guide_text = f.read()
    
    # Find all image prompts
    prompt_pattern = r'\*\*Full Image Prompt:\*\*\s*(.+?)(?=\n\n|\n-|\Z)'
    prompts = re.findall(prompt_pattern, guide_text, re.DOTALL | re.IGNORECASE)
    
    if not prompts or all('[' in p for p in prompts):
        log("⚠️  No completed image prompts found in guide")
        log("   Fill in the 'Full Image Prompt' sections first")
        return None
    
    # Save prompts to a file
    prompts_file = os.path.join(folder, "_image_prompts.txt")
    with open(prompts_file, 'w', encoding='utf-8') as f:
        f.write("# IMAGE PROMPTS FOR GENERATION\n\n")
        f.write("Copy each prompt below into your image generator (Midjourney, DALL-E, etc.)\n")
        f.write("Save images as: 0001_xxx.jpg, 0002_xxx.jpg, etc. in the Pictures/ folder\n\n")
        f.write("=" * 80 + "\n\n")
        
        for i, prompt in enumerate(prompts, 1):
            prompt_clean = prompt.strip().replace('\n', ' ')
            f.write(f"## Image {i:04d}\n\n")
            f.write(f"{prompt_clean}\n\n")
            f.write("-" * 80 + "\n\n")
    
    log(f"✓ Extracted {len(prompts)} image prompts")
    log(f"   Saved to: {os.path.basename(prompts_file)}")
    log(f"\n📝 NEXT STEPS FOR IMAGES:")
    log(f"   1. Open: {prompts_file}")
    log(f"   2. Copy each prompt into Midjourney/DALL-E")
    log(f"   3. Save images as 0001_xxx.jpg, 0002_xxx.jpg in Pictures/ folder")
    
    return prompts_file


def generate_thumbnail_prompt(guide_path, folder, idea):
    """Generate thumbnail_prompt.md for YouTube thumbnail creation."""
    log(f"\n🎨 Generating thumbnail prompt...")
    
    with open(guide_path, 'r', encoding='utf-8') as f:
        guide_text = f.read()
    
    # Extract video title from guide (first heading or use idea)
    title_match = re.search(r'^#\s+(.+)$', guide_text, re.MULTILINE)
    video_title = title_match.group(1).strip('"\'') if title_match else idea
    
    # Try to detect art style from guide
    art_style_keywords = {
        'hand-inked': 'hand-inked 2D storybook illustration',
        'storybook': 'hand-inked 2D storybook illustration',
        'flat': 'flat 2D vector illustration',
        'vector': 'flat 2D vector illustration',
        'stick': 'simple stick-figure style',
        'minimalist': 'minimalist flat design'
    }
    
    detected_style = "hand-inked 2D storybook illustration"  # Default
    guide_lower = guide_text.lower()
    for keyword, style in art_style_keywords.items():
        if keyword in guide_lower:
            detected_style = style
            break
    
    # Detect color palette from guide
    color_mentions = re.findall(r'#[0-9A-Fa-f]{6}', guide_text)
    has_custom_palette = len(color_mentions) > 0
    
    thumbnail_content = f"""# Thumbnail Generation Prompt
## Video: {video_title}

## Video Title
**"{video_title}"**

## Thumbnail Concept
[DESCRIBE YOUR THUMBNAIL CONCEPT HERE]
- Character/subject positioning (left third, center, right)
- Background/scene description
- Key visual elements that capture attention
- Emotional tone (dramatic, curious, shocking, etc.)

## Art Style Specifications
**Style:** {detected_style}

### Visual Details
- Painterly or vector approach (match your content style)
- Line work: thick outlines, cross-hatching, clean vectors
- Character design: simple or detailed
- Environment: richly detailed or minimalist
- Texture: watercolor washes, flat colors, gradients

### Color Palette
**Primary Colors:**
{chr(10).join(f'- Color name #{color}' for color in color_mentions[:5]) if has_custom_palette else '''- [Define your primary colors with hex codes]
- Example: Deep Blue #2B3350
- Example: Warm Ochre #C9A66B'''}

**Accent Colors:**
- [Define accent colors for highlights, text, emphasis]

## Composition Layout

### Text Overlay
**Primary Text:**
- "[MAIN HOOK TEXT]"
- Font: Bold, hand-drawn or impactful style
- Color: Bright yellow #FFD700 or contrasting color
- Outline: Thick black stroke (3-4px) for readability
- Position: Upper or center area, over less busy background
- Size: Large enough to read on mobile (40-50% of thumbnail height)

**Secondary Text (Optional):**
- "[Supporting text if needed]"
- Same style but 30% smaller

### Visual Elements
**Character/Subject Positioning:**
- Position: [Left third / Center / Right side]
- Close-up or full figure
- Expression and pose
- Key props or identifying features

**Background/Scene:**
- Setting description
- Depth and layers
- Supporting visual elements
- Atmospheric effects (lighting, mood)

## Mood & Atmosphere
- **Tone**: [Mysterious / Dramatic / Educational / Shocking / etc.]
- **Emotion**: [Curiosity / Fear / Wonder / Intrigue / etc.]
- **Era/Setting**: [Modern / Historical / Specific time period]
- **Energy**: [High energy / Contemplative / Intense / etc.]

## Technical Specifications
- **Dimensions**: 2752 x 1536 pixels (16:9 aspect ratio)
- **Resolution**: 72 DPI minimum
- **Format**: JPG, high quality
- **File Size**: Under 2MB for YouTube upload
- **Safe Zones**: Keep text/faces away from edges (10% margin)
- **Mobile Test**: Text must be legible at 320px width

## AI Image Generation Prompts

### Option 1: Midjourney/DALL-E
```
{detected_style}, [DESCRIBE YOUR SCENE]. Bold composition with [CHARACTER/SUBJECT] in [POSITION], [BACKGROUND DESCRIPTION]. Vibrant colors, dramatic lighting, cinematic framing. Large bold text "[YOUR TEXT]" with thick black outline. YouTube thumbnail style, eye-catching, high contrast, 16:9 aspect ratio --ar 16:9 --style raw
```

### Option 2: Stable Diffusion
```
{detected_style} :: [YOUR SCENE DESCRIPTION] :: [CHARACTER DETAILS] :: [BACKGROUND DETAILS] :: bold yellow text with black outline :: vibrant color palette :: dramatic lighting :: cinematic composition :: youtube thumbnail :: high contrast :: 16:9 aspect ratio --ar 16:9 --s 250
```

### Option 3: Detailed Prompt
```
Create a thumbnail in {detected_style} style. [DETAILED SCENE]. Character: [DESCRIPTION]. Background: [DESCRIPTION]. Colors: [YOUR PALETTE]. Text overlay: "[YOUR TEXT]" in bold yellow with thick black outline, positioned [LOCATION]. Lighting: [DESCRIPTION]. Mood: [MOOD]. YouTube thumbnail optimized, eye-catching composition, 2752x1536px.
```

## Production Checklist
- [ ] Art style matches content videos
- [ ] Text is large and readable on mobile
- [ ] High contrast between text and background
- [ ] Character/subject has clear facial expression or recognizable feature
- [ ] Colors are vibrant and eye-catching
- [ ] Composition follows rule of thirds
- [ ] All important elements in safe zones (away from edges)
- [ ] Tested at thumbnail size (check 320px width preview)
- [ ] File size under 2MB
- [ ] Resolution 2752x1536 or higher

## Alternative Concepts
If the main concept doesn't work, try:

### Concept 2: [Alternative approach]
- Different composition or angle
- Different text hook
- Different color emphasis

### Concept 3: [Another alternative]
- Character vs. scene focus shift
- Close-up vs. wide shot
- Different emotional tone

## Notes
- Generate at 2x resolution (5504x3072) then downscale for crisp text
- Test multiple text positions before finalizing
- Ensure thumbnail stands out in YouTube's grid of suggestions
- A/B test different hooks if possible
- Keep consistent with your channel's brand style

---

**Remember:** Thumbnails drive 80%+ of clicks. Invest time in getting this right!
"""
    
    thumbnail_path = os.path.join(folder, "thumbnail_prompt.md")
    with open(thumbnail_path, 'w', encoding='utf-8') as f:
        f.write(thumbnail_content)
    
    log(f"✓ Created thumbnail prompt template")
    log(f"   Saved to: {os.path.basename(thumbnail_path)}")
    
    return thumbnail_path


def main():
    ap = argparse.ArgumentParser(description="Generate missing content from an idea")
    ap.add_argument("content", help="Content folder path")
    ap.add_argument("--idea", help="Video idea/topic (only needed if guide doesn't exist)")
    ap.add_argument("--length", type=int, default=8, help="Target video length in minutes (default: 8)")
    args = ap.parse_args()
    
    folder = os.path.abspath(args.content)
    
    log("=" * 80)
    log("AutoGenerate - Content Creator")
    log("=" * 80)
    log(f"\nContent folder: {folder}")
    
    # Check what exists
    status = check_existing_content(folder)
    
    # Determine what needs to be generated
    needs_guide = not status["has_guide"]
    needs_voice = not status["has_voice"]
    needs_images = not status["has_images"]
    
    if not any([needs_guide, needs_voice, needs_images]):
        log("\n✅ ALL CONTENT EXISTS - Ready for AutoEditLongForm!")
        log("   Run: python autoedit.py \"" + folder + "\" --project \"PROJECT_NAME\"")
        return
    
    log("\n📋 Content Status:")
    log(f"   Guide:  {'❌ MISSING' if needs_guide else '✅ EXISTS'}")
    log(f"   Voice:  {'❌ MISSING' if needs_voice else '✅ EXISTS'}")
    log(f"   Images: {'❌ MISSING' if needs_images else '✅ EXISTS'}")
    
    # Generate guide if missing
    if needs_guide:
        if not args.idea:
            log("\n❌ ERROR: No guide found and no --idea provided")
            log("   Usage: python autogenerate.py <folder> --idea \"your video topic\"")
            sys.exit(1)
        
        guide_path = generate_script_and_guide(args.idea, folder, args.length)
        if not guide_path:
            sys.exit(1)
        
        log("\n⚠️  Guide template created. You need to:")
        log("   1. Fill in the script and image descriptions")
        log("   2. Run autogenerate again to create voice and image prompts")
        return
    
    guide_path = status["guide_path"]
    
    # Generate voice if missing
    if needs_voice:
        voice_created = generate_voice_from_guide(guide_path, folder)
        if not voice_created:
            log("\n⚠️  Voice files need to be created manually")
    
    # Extract image prompts if images missing
    if needs_images:
        prompts_file = generate_image_prompts(guide_path, folder)
        if not prompts_file:
            log("\n⚠️  Complete the guide first, then run again")
            return
    
    # Generate thumbnail prompt if it doesn't exist
    thumbnail_path = os.path.join(folder, "thumbnail_prompt.md")
    if not os.path.exists(thumbnail_path):
        generate_thumbnail_prompt(guide_path, folder, args.idea or "Your Video")
    else:
        log("\n✓ Thumbnail prompt already exists")
    
    # Final status
    log("\n" + "=" * 80)
    if needs_voice or needs_images:
        log("📝 TODO:")
        if needs_voice:
            log("   ⬜ Create voice files in Voice/ folder")
        if needs_images:
            log("   ⬜ Generate images from _image_prompts.txt")
        log("\nOnce complete, run AutoEditLongForm:")
        log(f"   python autoedit.py \"{folder}\" --project \"PROJECT_NAME\"")
    else:
        log("✅ ALL CONTENT READY!")
        log("\nRun AutoEditLongForm:")
        log(f"   python autoedit.py \"{folder}\" --project \"PROJECT_NAME\"")
    log("=" * 80)


if __name__ == "__main__":
    main()
