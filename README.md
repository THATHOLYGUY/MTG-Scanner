# 🃏 MTG Card Scanner

A free, local desktop app for scanning and cataloguing your Magic: The Gathering card collection using your webcam or photos. No accounts, no API keys, no subscription - everything runs on your computer.

\---

## What It Does

* **Scan cards** using your webcam or by uploading a photo
* **Automatically looks up** card details from Scryfall - name, mana cost, colors, type, set, rarity, and card artwork
* **Tracks your collection** with quantities (scanning a card you already own increments the count)
* **Sort and filter** your collection by name, mana value, color identity, rarity, or date added
* **Export to CSV** for use in Excel, Google Sheets, or any deck-building tool
* **Manual entry** - type a card name and Scryfall's fuzzy search finds it even with typos

\---

## How It Works

1. You point your webcam at a card (or upload a photo)
2. **Tesseract OCR** reads the card name from the top of the card image
3. The name is sent to the **Scryfall API** (free, no account needed) which returns all card details and artwork
4. The card is saved to a local **SQLite database** on your computer
5. Everything is displayed in a browser-based UI served locally at `http://localhost:5000`

If OCR struggles with a card (lighting, angle, etc.) you can use the **Manual tab** to type the name directly - Scryfall handles partial names and typos well.

\---

## What It Uses

|Tool|What for|Cost|
|-|-|-|
|[Python 3](https://python.org)|Runs the app|Free|
|[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)|Reads card names from images|Free|
|[pytesseract](https://pypi.org/project/pytesseract/)|Python wrapper for Tesseract|Free|
|[Pillow](https://pypi.org/project/Pillow/)|Image processing before OCR|Free|
|[Scryfall API](https://scryfall.com/docs/api)|Card data and artwork lookup|Free, no account needed|
|SQLite|Local card collection database|Built into Python|

No external services beyond Scryfall. No telemetry. Your collection stays on your machine.

\---

## Installation

### Step 1 - Install Python

Download and install Python 3.10 or newer from [python.org](https://python.org/downloads).

> \*\*Windows:\*\* On the installer's first screen, check \*\*"Add Python to PATH"\*\* before clicking Install.

### Step 2 - Install Tesseract OCR

Tesseract is the engine that reads text from card images.

**Windows:**

* Download the installer from the [UB Mannheim builds page](https://github.com/UB-Mannheim/tesseract/wiki)
* Run it with default settings
* Note the install path (usually `C:\\Program Files\\Tesseract-OCR`)

**Mac:**

```bash
brew install tesseract
```

(Install Homebrew first from [brew.sh](https://brew.sh) if you don't have it)

**Linux:**

```bash
sudo apt install tesseract-ocr
```

### Step 3 - Install Python packages

Open a terminal or Command Prompt in the `mtg-scanner` folder and run:

```bash
pip install pytesseract pillow
```

### Step 4 - Configure Tesseract path (Windows only)

Open `app.py` in a text editor and add these two lines near the top, after the imports:

```python
import pytesseract
pytesseract.pytesseract.tesseract\_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

Adjust the path if Tesseract installed somewhere else.

\---

## Running the App

**Windows:** Double-click `launch\_windows.bat`

**Mac / Linux:**

```bash
bash launch\_mac\_linux.sh
```

Then open your browser and go to: **http://localhost:5000**

Press `Ctrl+C` in the terminal to stop the app.

\---

## Usage

### Webcam Tab

* Click **Start Camera** and allow browser access
* Hold a card so the name is inside the golden guide box on screen
* Good lighting and holding the card flat makes a big difference
* Click **Scan Card**

### Upload Tab

* Drop a photo of your card or click to browse
* Works best with clear, straight-on photos
* Click **Scan Card**

### Manual Tab

* Type the card name (or part of it) and press Enter
* Scryfall's fuzzy search means "lighning bolt" still finds Lightning Bolt
* Fastest option when OCR is struggling

### Sorting \& Filtering

Use the dropdowns above your collection to:

* Sort by name, mana value, color, rarity, date added, or quantity
* Filter by color identity to find all your Gruul, Dimir, Simic cards etc.

### Exporting

Click **⬇ Export CSV** in the top right to download your full collection as a spreadsheet.

\---

## Tips for Better OCR Accuracy

* Lay the card **flat on a dark surface** - avoid angles
* Make sure the room is **well lit** (natural light works great)
* Hold the camera **directly above** the card, not at an angle
* **Fill the frame** - the card should take up most of the camera view
* The **golden box** on the webcam view shows exactly where the app looks for the name
* If a card won't scan, the Manual tab is just as fast for one-off lookups

\---

## Troubleshooting

**"OCR not installed" warning**

* Make sure you ran `pip install pytesseract pillow`
* Windows: check that the `tesseract\_cmd` path in `app.py` matches where Tesseract installed

**Card not found on Scryfall**

* Try the Manual tab and type the name yourself
* Very new cards may take a day or two to appear on Scryfall

**"pip is not recognized"**

* Reinstall Python and check "Add Python to PATH" on the first screen

**Camera won't start**

* Click the camera icon in your browser's address bar and allow access

\---

## Contributing

Contributions are welcome! Feel free to:

* **Open an issue** to report a bug or suggest a feature
* **Fork the repo** and submit a pull request with improvements

Some ideas for improvements:

* Better OCR accuracy / alternative card recognition methods
* Card price lookup (Scryfall provides pricing data for free)
* Deck building - group cards into named decks
* Barcode scanning as an alternative to OCR
* Collection statistics and charts
* Dark/light theme toggle

\---

## License

MIT License - free to use, modify, and distribute. See `LICENSE` for details.

\---

*Built with Python, Tesseract OCR, and the* [*Scryfall API*](https://scryfall.com/docs/api)*.*

