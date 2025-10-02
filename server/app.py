import os
import io
import uuid
from flask import Flask, jsonify, request, abort, send_file, g
from flask_cors import CORS
from db import tx, get_conn
import psycopg
from storage import save_file, load_file, delete_file, get_file_hash
from auth import (
    hash_password,
    verify_password,
    generate_jwt_token,
    require_auth,
    validate_email,
    validate_password
)

MAX_BYTES = 7 * 1024 * 1024  # 7MB MVP cap

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

def ensure_schema():
    path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(path, "r") as f, get_conn() as conn:
        conn.execute(f.read())
        conn.commit()

def is_valid_uuid(id_str):
    try:
        uuid.UUID(id_str)
        return True
    except ValueError:
        return False

# Initialize database schema on startup
with app.app_context():
    ensure_schema()

@app.get("/api/health")
def health():
    return {"ok": True}

# Authentication endpoints
@app.post("/api/auth/register")
def register():
    data = request.get_json()
    if not data:
        return abort(400, "Missing request body")

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validate email
    if not validate_email(email):
        return abort(400, "Invalid email format")

    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return abort(400, error_msg)

    # Hash password
    password_hash = hash_password(password)

    try:
        with tx() as cur:
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return abort(409, "Email already registered")

            # Create user
            cur.execute("""
                INSERT INTO users (email, password_hash)
                VALUES (%s, %s)
                RETURNING id::text, created_at
            """, (email, password_hash))
            (user_id, created_at) = cur.fetchone()

        # Generate JWT token
        token = generate_jwt_token(user_id)

        return jsonify({
            "token": token,
            "user": {
                "id": user_id,
                "email": email,
                "created_at": created_at.isoformat()
            }
        }), 201

    except psycopg.Error as e:
        return abort(500, "Database error")

@app.post("/api/auth/login")
def login():
    data = request.get_json()
    if not data:
        return abort(400, "Missing request body")

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return abort(400, "Email and password required")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id::text, email, password_hash, created_at
                    FROM users
                    WHERE email = %s
                """, (email,))
                row = cur.fetchone()

                if not row:
                    return abort(401, "Invalid email or password")

                user_id, user_email, password_hash, created_at = row

                # Verify password
                if not verify_password(password, password_hash):
                    return abort(401, "Invalid email or password")

                # Generate JWT token
                token = generate_jwt_token(user_id)

                return jsonify({
                    "token": token,
                    "user": {
                        "id": user_id,
                        "email": user_email,
                        "created_at": created_at.isoformat()
                    }
                })

    except psycopg.Error as e:
        return abort(500, "Database error")

@app.get("/api/auth/me")
@require_auth
def get_current_user():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id::text, email, created_at
                    FROM users
                    WHERE id = %s
                """, (g.user_id,))
                row = cur.fetchone()

                if not row:
                    return abort(404, "User not found")

                user_id, email, created_at = row

                return jsonify({
                    "id": user_id,
                    "email": email,
                    "created_at": created_at.isoformat()
                })

    except psycopg.Error as e:
        return abort(500, "Database error")

@app.get("/api/assets")
@require_auth
def list_assets():
    limit = max(1, min(int(request.args.get("limit", 20)), 100))
    offset = max(0, int(request.args.get("offset", 0)))
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from assets where user_id = %s", (g.user_id,))
            total = cur.fetchone()[0]
            cur.execute("""
                select id::text, created_at, filename, mime, size
                from assets
                where user_id = %s
                order by created_at desc
                limit %s offset %s
            """, (g.user_id, limit, offset))
            items = [
                {"id": r[0], "created_at": r[1].isoformat(), "filename": r[2], "mime": r[3], "size": r[4]}
                for r in cur.fetchall()
            ]
    return jsonify({"items": items, "total": total})

@app.post("/api/assets")
@require_auth
def create_asset():
    if "file" not in request.files:
        return abort(400, "Missing file")
    f = request.files["file"]
    data = f.read()
    if not f.mimetype or not f.mimetype.startswith("image/"):
        return abort(415, "Only image/* accepted")
    if len(data) > MAX_BYTES:
        return abort(413, "File too large")

    # Save file to disk and get hash
    file_hash = save_file(data)

    with tx() as cur:
        cur.execute("""
            insert into assets (filename, mime, size, file_hash, user_id)
            values (%s, %s, %s, %s, %s)
            returning id::text, created_at
        """, (f.filename or "image.jpg", f.mimetype, len(data), file_hash, g.user_id))
        (id_, created_at) = cur.fetchone()

    return jsonify({
        "id": id_,
        "created_at": created_at.isoformat(),
        "filename": f.filename or "image.jpg",
        "mime": f.mimetype,
        "size": len(data)
    }), 201

@app.get("/api/assets/<id>")
@require_auth
def get_asset(id: str):
    if not is_valid_uuid(id):
        return abort(404)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    select filename, mime, file_hash from assets where id = %s and user_id = %s
                """, (id, g.user_id))
                row = cur.fetchone()
                if not row:
                    return abort(404)
                filename, mime, file_hash = row
    except (psycopg.Error, ValueError) as e:
        return abort(404)

    try:
        data = load_file(file_hash)
    except FileNotFoundError:
        return abort(404, "File not found on disk")

    return send_file(io.BytesIO(data), mimetype=mime, download_name=filename)

@app.delete("/api/assets/<id>")
@require_auth
def delete_asset(id: str):
    if not is_valid_uuid(id):
        return abort(404)

    try:
        with tx() as cur:
            # Get file hash before deleting from database (ensure user owns the asset)
            cur.execute("select file_hash from assets where id = %s and user_id = %s", (id, g.user_id))
            row = cur.fetchone()
            if row is None:
                return abort(404)
            file_hash = row[0]

            # Delete from database
            cur.execute("delete from assets where id = %s and user_id = %s", (id, g.user_id))

            # Check if any other assets reference this file
            cur.execute("select count(*) from assets where file_hash = %s", (file_hash,))
            ref_count = cur.fetchone()[0]

            # Only delete file if no other assets reference it
            if ref_count == 0:
                delete_file(file_hash)
    except (psycopg.Error, ValueError) as e:
        return abort(404)
    return jsonify({"deleted": id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)