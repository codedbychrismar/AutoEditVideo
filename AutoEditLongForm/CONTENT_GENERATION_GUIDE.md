# Content Generation Guide

## How to Create Videos from Just an Idea

AutoEditLongForm now has **smart content detection** - it checks what exists and only generates what's missing.

---

## 🎯 Three Ways to Use It

### **Option 1: Everything Exists** (Current Workflow)
You already have Pictures, Voice, and Guide → Just edit directly

```bash
python autoedit.py "Content Folder" --project "PROJECT NAME"
```

✅ System detects everything exists  
✅ Proceeds directly to timeline editing

---

### **Option 2: Missing Some Content**
You have the guide but no voice or images

```bash
python autoedit.py "Content Folder" --project "PROJECT NAME"
```

✅ System detects what's missing  
✅ Creates templates/prompts for missing content  
✅ You fill in the gaps  
✅ Run again to edit

---

### **Option 3: Starting from Scratch** (NEW!)
You only have an idea

```bash
python autoedit.py "New Content Folder" --idea "History of Pizza" --project "PIZZA"
```

✅ System creates guide template  
✅ You write script & image descriptions  
✅ System extracts image prompts  
✅ You generate images  
✅ System generates voice (TTS) *[coming soon]*  
✅ System edits timeline

---

## 📋 Step-by-Step: From Idea to Video

### **Step 1: Create with Idea**

```bash
python autoedit.py "C:\...\Pizza Video" --idea "How did humans invent pizza?" --length 10
```

**What happens:**
- ✅ Creates folder if it doesn't exist
- ✅ Generates guide template with structure
- ✅ Shows you what to do next

**Output:**
```
Content folder: C:\...\Pizza Video
❌ Guide: MISSING
❌ Voice: MISSING  
❌ Images: MISSING

✓ Created guide template: how_did_humans_invent_pizza_guide.md

📝 NEXT STEPS:
   1. Open: how_did_humans_invent_pizza_guide.md
   2. Write your script in each 'Script Segment' line
   3. Describe images in each 'Full Image Prompt' section
   4. Run autogenerate again to create voice and images
```

---

### **Step 2: Fill in the Guide**

Open the generated guide file. You'll see:

```markdown
### Beat 1 — 0:00-0:05
**Script Segment:** "[Opening hook - grab attention immediately]"

**Full Image Prompt:** [Describe the opening image...]
```

**Replace placeholders with your content:**

```markdown
### Beat 1 — 0:00-0:05
**Script Segment:** "Picture a flatbread in ancient Rome, topped with olive oil and herbs."

**Full Image Prompt:** An ancient Roman marketplace at dawn, stick-figure baker 
holding a round flatbread topped with green herbs and drizzled olive oil, stone 
oven glowing orange in background, warm golden hour lighting, hand-inked 2D 
storybook illustration style.
```

**Do this for all beats** (~80-150 beats for an 8-10 minute video)

---

### **Step 3: Generate Image Prompts**

```bash
python autogenerate.py "C:\...\Pizza Video"
```

**What happens:**
- ✅ Reads your completed guide
- ✅ Extracts all image prompts
- ✅ Creates `_image_prompts.txt`

**Output:**
```
✓ Found guide: how_did_humans_invent_pizza_guide.md
✓ Extracted 120 image prompts
   Saved to: _image_prompts.txt

📝 NEXT STEPS FOR IMAGES:
   1. Open: _image_prompts.txt
   2. Copy each prompt into Midjourney/DALL-E
   3. Save images as 0001_xxx.jpg, 0002_xxx.jpg in Pictures/ folder
```

---

### **Step 4: Generate Images**

Open `_image_prompts.txt`:

```
## Image 0001

An ancient Roman marketplace at dawn, stick-figure baker holding a round 
flatbread topped with green herbs and drizzled olive oil, stone oven glowing 
orange in background...

--------------------------------------------------------------------------------

## Image 0002

Close-up of stick-figure hands kneading dough on a wooden table, flour dust 
in the air...
```

**For each prompt:**
1. Copy into Midjourney: `/imagine <paste prompt>`
2. Download the generated image
3. Rename: `0001_20261024123456.jpg`, `0002_20261024123456.jpg`, etc.
4. Save to `Pictures/` folder

---

### **Step 5: Generate Voice** (Optional - Manual for Now)

**Option A: Use ElevenLabs/Other TTS**
1. Copy all script segments from guide
2. Paste into TTS service
3. Download as `Script 1.mp3`, `Script 2.mp3`
4. Save to `Voice/` folder

**Option B: Record Yourself**
1. Read the script
2. Record in segments
3. Save as `Script 1.mp3`, `Script 2.mp3`

*Automatic TTS generation coming in future update*

---

### **Step 6: Edit the Timeline**

Once you have Pictures + Voice + Guide:

```bash
python autoedit.py "C:\...\Pizza Video" --project "PIZZA HISTORY"
```

**What happens:**
- ✅ Detects all content exists
- ✅ Transcribes voice
- ✅ Syncs images to narration
- ✅ Adds music, sound effects, text labels
- ✅ Applies smart zoom
- ✅ Creates complete CapCut timeline

---

## 🔄 The Smart Detection Flow

```
Run AutoEdit
    ↓
Check folder
    ↓
┌─────────────────┐
│ All exists?     │ → YES → Edit timeline
└─────────────────┘
    ↓ NO
Check what's missing
    ↓
┌─────────────────┐
│ Has guide?      │ → NO → Create guide template → STOP (user fills it)
└─────────────────┘
    ↓ YES
┌─────────────────┐
│ Has images?     │ → NO → Extract prompts → STOP (user generates)
└─────────────────┘
    ↓ YES
┌─────────────────┐
│ Has voice?      │ → NO → Show TTS options → STOP (user creates)
└─────────────────┘
    ↓ YES
Edit timeline → DONE
```

---

## 📁 Folder Structure

### **Before (Empty Folder)**
```
Pizza Video/
  (empty or doesn't exist)
```

### **After Step 1 (Guide Template)**
```
Pizza Video/
  ├── how_did_humans_invent_pizza_guide.md  ← Fill this in
```

### **After Step 3 (Image Prompts)**
```
Pizza Video/
  ├── how_did_humans_invent_pizza_guide.md  ✓ Completed
  ├── _image_prompts.txt                     ← Use for generation
```

### **After Steps 4-5 (Ready for Edit)**
```
Pizza Video/
  ├── how_did_humans_invent_pizza_guide.md  ✓
  ├── _image_prompts.txt                     ✓
  ├── Pictures/
  │   ├── 0001_xxx.jpg
  │   ├── 0002_xxx.jpg
  │   └── ... (120 images)
  ├── Voice/
  │   ├── Script 1.mp3
  │   └── Script 2.mp3
  ├── Description.txt        ← Optional
  └── Tags and keyword.txt   ← Optional
```

### **After Step 6 (Edited)**
```
Pizza Video/
  ├── ... (all above)
  ├── _autoedit/
  │   ├── report.txt
  │   ├── texts.json
  │   ├── YOUTUBE UPLOAD.txt
  │   └── transcripts/
  └── YOUTUBE UPLOAD.txt
```

---

## 💡 Pro Tips

### **Writing Good Image Prompts**

**✅ DO:**
- Be specific about characters, setting, mood
- Include style instructions (hand-inked, watercolor, etc.)
- Mention lighting and colors
- Keep it under 500 characters per prompt

**❌ DON'T:**
- Leave placeholders like "[describe scene]"
- Be vague: "a nice picture of pizza"
- Forget the house style
- Skip camera angles or mood

### **Efficient Image Generation**

**Batch Processing:**
1. Copy 10 prompts at once
2. Generate all in Midjourney
3. Download and rename batch
4. Repeat for next 10

**Midjourney Settings:**
- Use `--ar 16:9` for correct aspect ratio
- Use `--style raw` for less stylization
- Use `--v 6` for best quality

### **Voice Recording Tips**

**For Best Results:**
- Record in 2-3 minute chunks (one script file per section)
- Use consistent mic position and environment
- Normalize audio before using
- Aim for -20 dB average level

---

## 🚀 Quick Reference

### **Check What's Missing**
```bash
python autogenerate.py "Content Folder"
```

### **Create from Idea**
```bash
python autoedit.py "New Folder" --idea "Your topic" --length 10
```

### **Extract Image Prompts**
```bash
python autogenerate.py "Content Folder"
```

### **Edit Timeline (Auto-detects content)**
```bash
python autoedit.py "Content Folder" --project "NAME"
```

---

## 🔧 Troubleshooting

### "No guide found and no --idea provided"

**Fix:** Provide an idea:
```bash
python autoedit.py "Folder" --idea "Your video topic"
```

### "Guide template created. You need to fill it in"

**Fix:** This is expected! Open the guide file and write your script.

### "No completed script found in guide (still has placeholders)"

**Fix:** Replace all `[placeholder text]` with actual content.

### "No completed image prompts found"

**Fix:** Fill in the "Full Image Prompt" sections in the guide.

---

## 📊 Comparison: Old vs New Workflow

### **OLD Workflow (Manual Everything)**
1. Write script in Word → 2 hours
2. Create image prompts → 1 hour
3. Generate images in Midjourney → 3 hours
4. Record/generate voice → 1 hour
5. Create guide markdown → 30 minutes
6. Run AutoEdit → 5 minutes

**Total: ~7.5 hours**

### **NEW Workflow (Idea to Video)**
1. Run with --idea flag → 1 minute
2. Fill in guide template → 1.5 hours
3. Generate images (prompts ready) → 2 hours
4. Generate voice → 30 minutes
5. Run AutoEdit → 5 minutes

**Total: ~4 hours (47% faster!)**

---

## 🎯 Future Enhancements

Coming soon:
- [ ] Automatic TTS voice generation (ElevenLabs API)
- [ ] Automatic image generation (DALL-E/Midjourney API)
- [ ] AI script writing (Claude/GPT-4 from topic)
- [ ] Research integration (auto-gather facts)
- [ ] Style transfer (match existing channel style)

---

## 📞 Need Help?

**The system tells you exactly what to do at each step.**

Just read the output carefully:
- ✅ Green checkmarks = exists
- ❌ Red X = missing
- 📝 Next steps = what you need to do

If stuck, run `autogenerate.py` to see current status.

---

*Last updated: October 2026*  
*Part of AutoEditLongForm Enhanced v2.0*
