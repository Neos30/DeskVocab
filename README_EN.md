# DeskVocab — Learn Vocabulary While Slacking Off. Your Boss Thinks You're Working.

> Transparent desktop word cards · AI scene-based vocab · Document import · SM-2 spaced repetition · Full mouse-passthrough — zero workflow disruption

---

## 🌟 What does it do?

It lets you study vocabulary while looking like you're working.

SpeedDic overlays AI-generated word cards as a **transparent layer** on your Windows desktop wallpaper. By default, your mouse passes right through it — you can click desktop icons normally, open files, do whatever. It looks exactly like a regular desktop.

When you want to review, hit the hotkey. Buttons appear. Tap a rating. Hit the hotkey again. Done. **The whole cycle takes under 3 seconds.**

Just tell it your current *scene*, for example:

- `Investment Banking` → underwriting, due diligence, covenant, tombstone
- `Gym` → hypertrophy, compound lift, progressive overload, RPE
- `Fine Dining` → amuse-bouche, sommelier, mise en place, deglaze
- `Distributed Systems` → idempotent, circuit breaker, eventual consistency

Or **import a document** (PDF / Word) and let the AI extract high-frequency words automatically, filtering out stop words.

The AI generates curated vocab for your scene. The SM-2 algorithm decides what you review today. **You just show up — the words get into your head on their own.**

---

## 📦 Key Features

- **Transparent desktop overlay**: Word cards sit above desktop icons; mouse passthrough is on by default — zero interference with normal work
- **AI scene-based generation**: Enter any scene; powered by any OpenAI-compatible model — DeepSeek, OpenAI, Kimi, Qwen, GLM, and more
- **Document import**: Upload `.pdf` / `.docx` / `.doc` — AI extracts meaningful high-frequency words and filters out stop words automatically
- **SM-2 spaced repetition**: Scientific review scheduling; four-tier rating auto-adjusts next appearance (see table below)
- **Global hotkey `Ctrl+Alt+S`**: Toggle interactive / passthrough mode; complete a review in 3 seconds
- **Local-first**: Study history and API keys stored in local SQLite — no data uploaded, existing wordlist works offline

---

## 🎯 Four-Tier Rating

| Button | Meaning | Next Review | Dashboard Status |
|--------|---------|-------------|-----------------|
| Mastered | Got it, entering long-term queue | SM-2 extends interval | Proficient |
| Fuzzy | Vague memory, needs reinforcement | ~1 day | Fuzzy |
| Unknown | Completely blank | ~10 minutes | Unknown |
| Skip | Already know it, no review needed | Never again | Memorized |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| GUI | PyQt6 |
| Database | SQLite3 |
| AI Protocol | OpenAI Compatible API |
| Hotkey | pynput |
| Data Validation | Pydantic |
| PDF Parsing | pdfplumber |
| Word Parsing | python-docx |

---

## 🚀 Quick Start (Windows)

### 1. Install Dependencies

Ensure Python 3.9+ is installed (check **Add Python to PATH** during setup):

```powershell
pip install -r requirements.txt
```

### 2. Launch

Open PowerShell / CMD **as Administrator**, navigate to the project root, then run:

```powershell
python src/main.py
```

### 3. Generate Vocabulary

**First-time setup (configure model)**

1. Right-click the system tray icon → **"Model Config"**
2. Choose a provider, enter your API Key and Base URL (e.g. DeepSeek: `https://api.deepseek.com`)
3. Click **"Test Connection"** to verify → Save

**Option A: Scene keyword**

1. Right-click the system tray icon → **"Generate Words"**
2. Type your scene in the "Current Scene" field
3. Click **"Generate"** → words are fetched in the background; the desktop updates automatically when done

**Option B: Import a document**

1. Right-click the system tray icon → **"Generate Words"**
2. Click **"Browse…"** and select a `.pdf` / `.docx` / `.doc` file, then set the word count (default: 10)
3. Click **"Import & Generate"** → AI extracts high-frequency words from the document; desktop updates when complete

### 4. Daily Usage

| Action | Result |
|---|---|
| Do nothing | Word cards sit quietly on your wallpaper; mouse passes through; normal work continues |
| `Ctrl+Alt+S` | Interactive mode activates; title bar turns green; rating buttons become clickable |
| Click a rating | SM-2 logs the review and schedules the next appearance |
| Click "Skip" | Marked as memorized — removed from all future reviews |
| `Ctrl+Alt+S` again | Back to passthrough — back to looking productive |

---

## Notes

- **Administrator rights**: If any foreground app runs as administrator (Task Manager, certain games), SpeedDic also needs administrator privileges to capture `Ctrl+Alt+S`
- **High-DPI blur**: If the UI appears blurry, adjust the display scaling in Windows system settings
- **`.doc` format**: Requires `textract` (pip) or the system tool `antiword`; `.docx` is recommended

---

## 📋 Changelog

### v1.2
- **Model config split out**: New "Model Config" tray entry, separate from "Generate Words" — first-time setup is now a focused, dedicated flow

### v1.1
- Added **document import**: supports `.pdf` / `.docx` / `.doc`; AI extracts high-frequency words automatically
- Added **Skip** button: marks a word as memorized instantly, bypassing SRS entirely
- SRS improvement: "Unknown" review interval shortened from 1 day to **10 minutes**
- Mastery levels refined to four tiers (Memorized / Proficient / Fuzzy / Unknown), each mapped to a rating action

### v1.0
- Local database management, AI scene-based word generation, transparent desktop overlay

---

*DeskVocab — Give your brain the idle time. Give your boss the desktop.*
