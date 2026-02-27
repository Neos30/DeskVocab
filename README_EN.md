# DeskVocab — Learn Vocabulary While Slacking Off. Your Boss Thinks You're Working.

> Transparent desktop word cards · AI scene-based vocab · SM-2 spaced repetition · Full mouse-passthrough — zero workflow disruption

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

The AI generates curated vocab for your scene. The SM-2 algorithm decides what you review today. **You just show up — the words get into your head on their own.**

---

## 📦 Key Features

- **Transparent desktop overlay**: Word cards sit above desktop icons; mouse passthrough is on by default — zero interference with normal work
- **AI scene-based generation**: Enter any scene; powered by any OpenAI-compatible model — DeepSeek, OpenAI, Kimi, Qwen, GLM, and more
- **SM-2 spaced repetition**: Scientific review scheduling; three-tier rating (Mastered / Fuzzy / Unknown) auto-adjusts next appearance
- **Global hotkey `Ctrl+Alt+S`**: Toggle interactive / passthrough mode; complete a review in 3 seconds
- **Local-first**: Study history and API keys stored in local SQLite — no data uploaded, existing wordlist works offline

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

### 3. Configure Your Scene

1. Right-click the system tray icon → **Settings**
2. Enter your API Key and Base URL (e.g. DeepSeek: `https://api.deepseek.com`)
3. Type your scene in the "Current Scene" field
4. Click **"Save & Generate"** → words are fetched in the background; the desktop updates automatically when done

### 4. Daily Usage

| Action | Result |
|---|---|
| Do nothing | Word cards sit quietly on your wallpaper; mouse passes through; normal work continues |
| `Ctrl+Alt+S` | Interactive mode activates; title bar turns green; rating buttons become clickable |
| Click a rating | SM-2 logs the review and schedules the next appearance |
| `Ctrl+Alt+S` again | Back to passthrough — back to looking productive |

---

## Notes

- **Administrator rights**: If any foreground app runs as administrator (Task Manager, certain games), SpeedDic also needs administrator privileges to capture `Ctrl+Alt+S`
- **High-DPI blur**: If the UI appears blurry, adjust the display scaling in Windows system settings

---

*SpeedDic — Give your brain the idle time. Give your boss the desktop.*
