# GIF Capture Guide for AegisGraph

This guide provides instructions for capturing high-quality animated GIFs of the AegisGraph dashboard for documentation, demos, and presentations.

## Option 1: Automated Capture with Playwright (Recommended)

### Prerequisites
```bash
pip install playwright
playwright install chromium
```

### Automated Script
Run the provided capture script:

```bash
python scripts/capture_demo_gif.py --output assets/screenshots/demo-flow.gif
```

This script automatically:
1. Starts the browser at `http://localhost:3000`
2. Navigates through Map → Anomalies → Graph → Analyst views
3. Records each interaction with smooth transitions
4. Exports an optimized GIF

### Manual Playwright Capture
For custom captures, use this template:

```python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    
    # Start recording
    page.emulate_media(media="screen")
    page.goto("http://localhost:3000")
    
    # Navigate through views
    page.click('a[href="/anomalies"]')
    time.sleep(2)
    page.click('a[href="/graph"]')
    time.sleep(2)
    page.click('a[href="/analyst"]')
    time.sleep(2)
    
    browser.close()
```

---

## Option 2: Linux Tools

### Using Peek
```bash
sudo apt-get install peek

# Open Peek, select area (1280x720 recommended)
# Set format to GIF, framerate to 10-12 fps
# Click Record, perform demo, click Stop
```

### Using Kapow (CLI)
```bash
sudo apt-get install ffmpeg

# Record selected area for 30 seconds
ffmpeg -f x11grab -video_size 1280x720 -framerate 10 \
  -i :0.0+100,100 -t 30 \
  -vf "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  assets/screenshots/demo.gif
```

---

## Option 3: macOS Tools

### Using QuickTime + GIPHY Capture
1. Open QuickTime Player → File → New Screen Recording
2. Select area (1280x720)
3. Record demo, save as .mov
4. Convert to GIF using GIPHY Capture or:
   ```bash
   brew install ffmpeg
   ffmpeg -i input.mov -vf "fps=10,scale=1280:-1:flags=lanczos" output.gif
   ```

### Using Kap (Open Source)
```bash
brew install --cask kap

# Open Kap, select area
# Set format to GIF, quality to 60%
# Record, then export
```

---

## Option 4: Windows Tools

### Using ShareX
1. Download ShareX from https://getsharex.com/
2. Tasks → Screen Recording → Start/Stop
3. Select area, record demo
4. Auto-converts to GIF with optimization

### Using ScreenToGif
1. Download from https://www.screentogif.com/
2. Open Recorder, select area
3. Press F7 to start, F8 to stop
4. Edit frames if needed, export as GIF

---

## Recommended Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Resolution | 1280×720 | Optimal for web embedding |
| Frame Rate | 10-12 fps | Smooth enough, small file size |
| Colors | 256 max | GIF limitation, dithering helps |
| Duration | 15-30 sec | Keep it concise |
| File Size | < 5 MB | For GitHub/GitLab compatibility |

---

## Demo Flow Suggestions

### Full Product Tour (30 seconds)
1. **Map View (8s)**: Show entities loading, click anomaly marker
2. **Anomaly Queue (8s)**: Scroll list, expand detail drawer
3. **Graph Explorer (7s)**: Drag nodes, show relationships
4. **AI Analyst (7s)**: Type query, show response with citations

### Anomaly Detection Focus (20 seconds)
1. **Map View (5s)**: Show red anomaly markers
2. **Anomaly Queue (8s)**: Filter by severity, expand explanation
3. **Action Approval (7s)**: Click approve/reject, show audit update

### AI Analyst Focus (20 seconds)
1. **Analyst Page (5s)**: Show chat interface
2. **Query Input (5s)**: Type "Show recent anomalies"
3. **Response (5s)**: Highlight citations and confidence meter
4. **Follow-up (5s)**: Ask clarification question

---

## Optimization Tips

1. **Reduce Colors**: Use tools like `gifsicle` to optimize:
   ```bash
   gifsicle -O3 --colors=256 input.gif -o output.gif
   ```

2. **Crop Smartly**: Remove browser chrome, focus on content area

3. **Compress**: Use online tools like ezgif.com for final compression

4. **Add Captions**: Use `ffmpeg` to add text overlays:
   ```bash
   ffmpeg -i input.gif -vf "drawtext=text='AegisGraph Demo':fontsize=24:fontcolor=white:x=10:y=10" output.gif
   ```

5. **Loop Count**: Set to infinite for continuous playback in docs

---

## Troubleshooting

**GIF too large?**
- Reduce resolution to 960×540
- Lower frame rate to 8 fps
- Shorten duration

**Colors look banded?**
- Enable dithering in your capture tool
- Increase color palette to 256

**Playback stuttering?**
- Ensure consistent frame rate (10-12 fps ideal)
- Avoid rapid mouse movements during capture

**Browser lag visible?**
- Close other tabs/applications
- Use headless mode for automated captures
- Pre-load all views before recording

---

## Example Commands Summary

```bash
# Generate with Playwright script
python scripts/capture_demo_gif.py

# Optimize existing GIF
gifsicle -O3 --colors=256 demo.gif -o demo-optimized.gif

# Convert video to GIF
ffmpeg -i demo.mov -vf "fps=10,scale=1280:-1" demo.gif

# Add watermark/text
ffmpeg -i demo.gif -vf "drawtext=text='AEGISGRAPH':fontsize=32:fontcolor=white:x=w-tw-10:y=h-th-10" demo-watermarked.gif
```
