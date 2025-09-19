import os
import io
from flask import Flask, jsonify, request, abort, send_file
from flask_cors import CORS
from db import tx, get_conn
import psycopg

MAX_BYTES = 7 * 1024 * 1024  # 7MB MVP cap

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

def ensure_schema():
    path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(path, "r") as f, get_conn() as conn:
        conn.execute(f.read())
        conn.commit()

# Initialize database schema on startup
with app.app_context():
    ensure_schema()

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/assets")
def list_assets():
    limit = max(1, min(int(request.args.get("limit", 20)), 100))
    offset = max(0, int(request.args.get("offset", 0)))
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from assets")
            total = cur.fetchone()[0]
            cur.execute("""
                select id::text, created_at, filename, mime, octet_length(data) as size
                from assets
                order by created_at desc
                limit %s offset %s
            """, (limit, offset))
            items = [
                {"id": r[0], "created_at": r[1].isoformat(), "filename": r[2], "mime": r[3], "size": r[4]}
                for r in cur.fetchall()
            ]
    return jsonify({"items": items, "total": total})

@app.post("/api/assets")
def create_asset():
    if "file" not in request.files:
        return abort(400, "Missing file")
    f = request.files["file"]
    data = f.read()
    if not f.mimetype or not f.mimetype.startswith("image/"):
        return abort(415, "Only image/* accepted")
    if len(data) > MAX_BYTES:
        return abort(413, "File too large")

    with tx() as cur:
        cur.execute("""
            insert into assets (filename, mime, size, data)
            values (%s, %s, %s, %s)
            returning id::text, created_at
        """, (f.filename or "image.jpg", f.mimetype, len(data), psycopg.Binary(data)))
        (id_, created_at) = cur.fetchone()

    return jsonify({"id": id_, "created_at": created_at.isoformat()}), 201

@app.get("/api/assets/<id>")
def get_asset(id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                select filename, mime, data from assets where id = %s
            """, (id,))
            row = cur.fetchone()
            if not row:
                return abort(404)
            filename, mime, data = row
    return send_file(io.BytesIO(bytes(data)), mimetype=mime, download_name=filename)

@app.delete("/api/assets/<id>")
def delete_asset(id: str):
    with tx() as cur:
        cur.execute("delete from assets where id = %s returning 1", (id,))
        if cur.fetchone() is None:
            return abort(404)
    return jsonify({"deleted": id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)