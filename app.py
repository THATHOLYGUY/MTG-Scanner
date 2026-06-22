"""
MTG Card Scanner - Main Application (Free, no API key needed)
Uses Tesseract OCR (local, free) + Scryfall API (free) for card recognition.

Run this file to start the app, then open http://localhost:5000 in your browser.
"""

import base64
import csv
import io
import json
import os
import sqlite3
import urllib.parse
import urllib.request
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# ── Database setup ─────────────────────────────────────────────────────────────

DB_PATH = "collection.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT NOT NULL,
            mana_cost      TEXT,
            cmc            REAL,
            colors         TEXT,
            color_identity TEXT,
            type_line      TEXT,
            set_name       TEXT,
            rarity         TEXT,
            quantity       INTEGER DEFAULT 1,
            scryfall_id    TEXT,
            image_url      TEXT,
            added_at       TEXT
        )
    """)
    con.commit()
    con.close()

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

# ── OCR ────────────────────────────────────────────────────────────────────────

def ocr_available():
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def read_card_name_ocr(image_b64: str) -> str | None:
    try:
        import pytesseract
        from PIL import Image, ImageFilter, ImageEnhance

        img_bytes = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("L")
        img.save("debug_capture.png")

        w, h = img.size
        print(f"Image size: {w}x{h}")

        # Try multiple crop zones and pick the best result
        crops = [
            (60,  48, 400,  82),
            (60,  45, 400,  78),
            (60,  52, 400,  85),
        ]

        best = ""
        for box in crops:
            crop = img.crop(box)
            crop = crop.resize((crop.width * 4, crop.height * 4), Image.LANCZOS)
            crop = ImageEnhance.Contrast(crop).enhance(2.0)
            crop = crop.filter(ImageFilter.SHARPEN)
            text = pytesseract.image_to_string(crop, config="--oem 3 --psm 7").strip()
            text = " ".join(text.split())
            text = "".join(c for c in text if c.isalpha() or c == " ").strip()
            print(f"Crop {box} -> '{text}'")
            if len(text) > len(best):
                best = text

        return best if len(best) >= 2 else None

    except Exception as e:
        print(f"OCR error: {e}")
        return None
# ── Scryfall ───────────────────────────────────────────────────────────────────

def scryfall_search(name: str) -> dict | None:
    safe = name.strip().replace(" ", "+")
    url = f"https://api.scryfall.com/cards/named?fuzzy={safe}"
    print(f"Requesting: {url}")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Scryfall error: {e.code} - {body}")
        return None
    except Exception as e:
        print(f"Scryfall error: {e}")
        return None

def parse_colors(card: dict) -> tuple[str, str]:
    color_map = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green"}
    colors   = [color_map.get(c, c) for c in card.get("colors", [])]
    identity = [color_map.get(c, c) for c in card.get("color_identity", [])]
    return ", ".join(colors) or "Colorless", ", ".join(identity) or "Colorless"

# ── Collection ─────────────────────────────────────────────────────────────────

def add_or_increment(scryfall_card: dict) -> dict:
    colors, color_identity = parse_colors(scryfall_card)
    image_url = (
        scryfall_card.get("image_uris", {}).get("normal")
        or scryfall_card.get("image_uris", {}).get("small", "")
    )
    con = get_db()
    existing = con.execute(
        "SELECT id, quantity FROM cards WHERE scryfall_id = ?",
        (scryfall_card.get("id"),)
    ).fetchone()

    if existing:
        con.execute("UPDATE cards SET quantity = quantity + 1 WHERE id = ?", (existing["id"],))
        row_id = existing["id"]
    else:
        cur = con.execute(
            """INSERT INTO cards
               (name, mana_cost, cmc, colors, color_identity, type_line,
                set_name, rarity, quantity, scryfall_id, image_url, added_at)
               VALUES (?,?,?,?,?,?,?,?,1,?,?,?)""",
            (
                scryfall_card.get("name"),
                scryfall_card.get("mana_cost", ""),
                scryfall_card.get("cmc", 0),
                colors,
                color_identity,
                scryfall_card.get("type_line", ""),
                scryfall_card.get("set_name", ""),
                scryfall_card.get("rarity", ""),
                scryfall_card.get("id"),
                image_url,
                datetime.now().isoformat(timespec="seconds"),
            )
        )
        row_id = cur.lastrowid

    con.commit()
    row = con.execute("SELECT * FROM cards WHERE id = ?", (row_id,)).fetchone()
    con.close()
    return dict(row)

def get_collection(sort_by: str = "name", filter_color: str = "") -> list[dict]:
    valid = {"name", "cmc", "colors", "rarity", "added_at", "quantity"}
    if sort_by not in valid:
        sort_by = "name"
    con = get_db()
    query = "SELECT * FROM cards"
    params: list = []
    if filter_color:
        query += " WHERE color_identity LIKE ?"
        params.append(f"%{filter_color}%")
    query += f" ORDER BY {sort_by}"
    rows = [dict(r) for r in con.execute(query, params).fetchall()]
    con.close()
    return rows

def delete_card(card_id: int):
    con = get_db()
    con.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    con.commit()
    con.close()

def export_csv() -> str:
    cards = get_collection()
    out = io.StringIO()
    if cards:
        writer = csv.DictWriter(out, fieldnames=cards[0].keys())
        writer.writeheader()
        writer.writerows(cards)
    return out.getvalue()

# ── HTTP handler ───────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def do_GET(self):
        path = self.path.split("?")[0]
        qs   = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        if path == "/":
            self.serve_file("index.html", "text/html")
        elif path == "/api/collection":
            self.send_json(get_collection(
                qs.get("sort", ["name"])[0],
                qs.get("color", [""])[0]
            ))
        elif path == "/api/export":
            data = export_csv().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", "attachment; filename=mtg_collection.csv")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/config":
            self.send_json({"ocr_available": ocr_available()})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        path = self.path

        if path == "/api/scan":
            body        = json.loads(self.read_body())
            image_b64   = body.get("image", "")
            manual_name = body.get("manual_name", "").strip()

            if manual_name:
                card_name = manual_name
            elif image_b64:
                card_name = read_card_name_ocr(image_b64)
                if not card_name:
                    self.send_json({
                        "error": "OCR couldn't read the card name. Try the Manual tab instead, or make sure the card name is clearly visible and well-lit."
                    }, 400)
                    return
            else:
                self.send_json({"error": "No image or name provided."}, 400)
                return

            scryfall = scryfall_search(card_name)
            if not scryfall or scryfall.get("object") == "error":
                self.send_json({
                    "error": f"Couldn't find \"{card_name}\" on Scryfall. OCR may have misread it — try the Manual tab."
                }, 404)
                return

            added = add_or_increment(scryfall)
            self.send_json({"success": True, "card": added, "ocr_read": card_name})

        elif path == "/api/delete":
            body = json.loads(self.read_body())
            delete_card(int(body["id"]))
            self.send_json({"success": True})

        else:
            self.send_response(404); self.end_headers()

    def serve_file(self, filename, content_type):
        try:
            with open(filename, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404); self.end_headers()

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = 5000
    server = HTTPServer(("localhost", port), Handler)
    print(f"\n🃏  MTG Card Scanner is running!")
    print(f"    Open your browser:  http://localhost:{port}\n")
    print("    Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
