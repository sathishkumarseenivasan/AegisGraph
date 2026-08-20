# AegisGraph Screenshot Capture Guide

This guide provides exact steps to capture high-quality screenshots for the README and documentation.

---

## Prerequisites

1. **Seed the database**:
   ```bash
   make seed
   ```

2. **Start the application**:
   ```bash
   make dev
   ```

3. **Open browser** to `http://localhost:3000`

4. **Enable dark mode** (if not default):
   - Browser DevTools → Application → Local Storage → Set theme=dark

---

## Required Screenshots

### 1. Dashboard Map View (`screenshot-map.png`)

**What to capture**: Main map with entity markers, sidebar visible.

**Steps**:
1. Land on home page (`/`)
2. Wait for map to fully load (~3 seconds)
3. Ensure at least 3-4 anomaly badges are visible
4. Hide browser bookmarks bar (Ctrl+Shift+B / Cmd+Shift+B)
5. Press F12 to open DevTools (optional, for console visibility)
6. Capture full viewport: `Cmd+Shift+4` (Mac) or `Win+Shift+S` (Windows)

**Viewport**: 1920×1080 recommended

**Caption**: _Live multi-source situational awareness dashboard with 100 fused tracks._

---

### 2. Anomaly Queue (`screenshot-anomalies.png`)

**What to capture**: Anomaly list with expansion panel showing details.

**Steps**:
1. Click **Anomalies** tab in sidebar
2. Sort by severity (click column header if needed)
3. Click first HIGH severity anomaly to expand
4. Ensure explanation, evidence IDs, and action buttons are visible
5. Capture the expanded panel area

**Viewport**: 1920×1080

**Caption**: _Explainable anomaly detection with severity scoring, evidence links, and recommended actions._

---

### 3. Knowledge Graph (`screenshot-graph.png`)

**What to capture**: Force-directed graph with nodes and edges.

**Steps**:
1. Click **Graph** tab
2. Wait for graph layout to stabilize (~2 seconds)
3. Hover over one node to show tooltip
4. Optional: Click a node to show side panel
5. Capture with tooltip visible

**Viewport**: 1920×1080

**Caption**: _Ontology graph showing entities, observations, anomalies, and actions with typed relationships._

---

### 4. AI Analyst Chat (`screenshot-analyst.png`)

**What to capture**: Chat interface with a completed Q&A exchange.

**Steps**:
1. Click **Analyst** tab
2. Type query: `Show me all high-severity anomalies`
3. Wait for response (~2-3 seconds)
4. Ensure citations and confidence meter are visible
5. Capture both query and response

**Viewport**: 1920×1080

**Caption**: _Retrieval-grounded AI analyst with citations, confidence scoring, and explicit limitations._

---

### 5. Audit Timeline (`screenshot-audit.png`)

**What to capture**: Chronological audit event list.

**Steps**:
1. Click **Audit** tab
2. Scroll to show ~10-15 events
3. Optional: Click "Verify Hash Chain" button and capture success message
4. Capture timeline with timestamps visible

**Viewport**: 1920×1080

**Caption**: _Append-only hash-chained audit log with cryptographic integrity verification._

---

## Optional: Animated GIF

### Demo Flow GIF (`demo.gif`)

**Duration**: 30-60 seconds

**Sequence**:
1. Home page (3 sec)
2. Click Anomalies → Expand one (5 sec)
3. Approve action → Confirmation toast (3 sec)
4. Navigate to Graph → Hover node (5 sec)
5. Navigate to Analyst → Type query → Response (10 sec)
6. Navigate to Audit → Verify button → Pass (5 sec)

**Tools**:
- Mac: QuickTime Player → File → New Screen Recording
- Windows: OBS Studio (free) or built-in Game Bar (Win+G)
- Linux: SimpleScreenRecorder or Peek (for GIF)

**Export settings**:
- Format: GIF or MP4
- Frame rate: 30 fps
- Resolution: 1920×1080 (or scale to 1280×720 for smaller file)
- Optimize colors (for GIF): 256 color palette

---

## Post-Processing

### Resize/Optimize

```bash
# Install imagemagick
brew install imagemagick  # Mac
sudo apt install imagemagick  # Linux

# Resize to max width 1200px
mogrify -resize 1200x assets/screenshots/*.png

# Optimize PNGs
pngquant --quality=65-80 --ext .png --force assets/screenshots/*.png
```

### Add Annotations (Optional)

Use tools like:
- **Skitch** (Mac/Windows): Arrows, blur, text
- **Greenshot** (Windows): Free annotation tool
- **GIMP** (Cross-platform): Advanced editing

---

## Update README

Replace placeholder paths in README.md:

```markdown
<!-- Before -->
![Dashboard](assets/screenshots/placeholder-map.png)

<!-- After -->
![Dashboard](assets/screenshots/screenshot-map.png)
```

---

## Checklist

- [ ] All 5 screenshots captured
- [ ] Images optimized (<500KB each)
- [ ] Captions added to README
- [ ] Optional: Demo GIF created (<5MB)
- [ ] Verified images render correctly on GitHub

---

*Tip: Re-capture after any major UI changes to keep documentation current.*
