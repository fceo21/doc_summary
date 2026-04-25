import csv
import io
import os
from datetime import date

from flask import Flask, jsonify, render_template, request, send_file, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dc-review-secret-2024")

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "reviews.db")
ADMIN_PIN = os.environ.get("ADMIN_PIN", "1234")


def get_db():
    import sqlite3
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS participations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            participated_at DATETIME DEFAULT (datetime('now','localtime')),
            naver_id    TEXT,
            room_number TEXT,
            name_prefix TEXT
        )
    """)
    conn.commit()
    conn.close()


def generate_assets():
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)

    # QR code
    qr_path = os.path.join(static_dir, "qr_naver.png")
    if not os.path.exists(qr_path):
        try:
            import qrcode
            qr = qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data("https://m.place.naver.com/my/review")
            qr.make(fit=True)
            img = qr.make_image(fill_color="#1E5631", back_color="white")
            img.save(qr_path)
            print("✅ QR code generated")
        except ImportError:
            print("⚠️  qrcode not installed — run: pip install qrcode[pil]")

    # PWA icons
    for size in [192, 512]:
        icon_path = os.path.join(static_dir, f"icon-{size}.png")
        if not os.path.exists(icon_path):
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new("RGB", (size, size), "#1E5631")
                draw = ImageDraw.Draw(img)
                text = "DC"
                draw.text((size // 2, size // 2), text, fill="white", anchor="mm")
                img.save(icon_path)
                print(f"✅ Icon {size}px generated")
            except Exception as e:
                print(f"⚠️  Icon generation skipped: {e}")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    qr_exists = os.path.exists(
        os.path.join(os.path.dirname(__file__), "static", "qr_naver.png")
    )
    return render_template("index.html", qr_exists=qr_exists)


@app.route("/api/participate", methods=["POST"])
def participate():
    data = request.get_json() or {}
    naver_id    = (data.get("naver_id")    or "").strip() or None
    room_number = (data.get("room_number") or "").strip() or None
    name_prefix = (data.get("name_prefix") or "").strip() or None

    if not any([naver_id, room_number, name_prefix]):
        return jsonify({"error": "input_required"}), 400

    today = date.today().isoformat()
    conn = get_db()
    try:
        for col, val in [("naver_id", naver_id), ("room_number", room_number), ("name_prefix", name_prefix)]:
            if val:
                row = conn.execute(
                    f"SELECT id FROM participations WHERE {col}=? AND date(participated_at)=?",
                    (val, today),
                ).fetchone()
                if row:
                    return jsonify({"duplicate": True})

        conn.execute(
            "INSERT INTO participations (naver_id, room_number, name_prefix) VALUES (?,?,?)",
            (naver_id, room_number, name_prefix),
        )
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()


@app.route("/api/admin/verify", methods=["POST"])
def admin_verify():
    pin = (request.get_json() or {}).get("pin", "")
    if pin == ADMIN_PIN:
        session["admin"] = True
        return jsonify({"success": True})
    return jsonify({"error": "잘못된 PIN입니다"}), 401


@app.route("/api/admin/records")
def admin_records():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 401
    date_q = request.args.get("date", date.today().isoformat())
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM participations WHERE date(participated_at)=? ORDER BY participated_at DESC",
        (date_q,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/admin/export")
def admin_export():
    if not session.get("admin"):
        return jsonify({"error": "Unauthorized"}), 401
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM participations ORDER BY participated_at DESC"
    ).fetchall()
    conn.close()

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["ID", "참여일시", "네이버아이디", "호실번호", "성함앞2글자"])
    for r in rows:
        w.writerow([r["id"], r["participated_at"],
                    r["naver_id"] or "", r["room_number"] or "", r["name_prefix"] or ""])
    out.seek(0)
    return send_file(
        io.BytesIO(out.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"reviews_{date.today()}.csv",
    )


if __name__ == "__main__":
    init_db()
    generate_assets()
    print("\n🟢 서버 시작: http://localhost:5050\n")
    app.run(debug=False, host="0.0.0.0", port=5050)
