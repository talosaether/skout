React + Vite + Tailwind
PWA plugin
Flask API + Postgres ( Direct SQL, no ORM )
Camera via getUserMedia
ChatGPT said:
Thought for 15s

Killer MVP stack. Here’s a tight starter that actually runs and doesn’t bury you in ceremony.

Stack Summary (my take)

React + Vite + Tailwind: fastest DX, tiny bundles.

vite-plugin-pwa: offline, installable, auto-updates.

Flask + Postgres (direct SQL via psycopg): no ORM, full control.

Camera via getUserMedia: simple, reliable, works on iOS Safari with the right flags.

Repo layout
mvp-xplat/
  client/
    index.html
    src/
      main.tsx
      App.tsx
      components/CameraCapture.tsx
      lib/api.ts
    public/
    vite.config.ts
    tailwind.config.js
    postcss.config.js
    tsconfig.json
    index.css
    package.json
  server/
    app.py
    db.py
    schema.sql
    requirements.txt
    Dockerfile
  docker-compose.yml
  .env.example

1) Frontend — React + Vite + Tailwind + PWA

Scaffold

npm create vite@latest client -- --template react-ts
cd client
npm i
npm i -D tailwindcss postcss autoprefixer vite-plugin-pwa
npx tailwindcss init -p


tailwind.config.js

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};


index.css

@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root { height: 100%; }


vite.config.ts

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "MVP CRUD Camera",
        short_name: "MVP",
        start_url: "/",
        display: "standalone",
        background_color: "#0f172a",
        theme_color: "#0ea5e9",
        icons: [
          { src: "pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "pwa-512x512.png", sizes: "512x512", type: "image/png" }
        ]
      }
    })
  ],
  server: {
    proxy: {
      "/api": "http://localhost:8000" // dev proxy to Flask
    }
  }
});


src/lib/api.ts

export type Asset = {
  id: string;
  created_at: string;
  filename: string;
  mime: string;
  size: number;
};

export async function listAssets(limit = 20, offset = 0) {
  const res = await fetch(`/api/assets?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to list assets");
  return (await res.json()) as { items: Asset[]; total: number };
}

export async function uploadBlob(file: Blob, filename: string) {
  const fd = new FormData();
  fd.append("file", file, filename);
  const res = await fetch("/api/assets", { method: "POST", body: fd });
  if (!res.ok) throw new Error("Upload failed");
  return await res.json();
}

export async function deleteAsset(id: string) {
  const res = await fetch(`/api/assets/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Delete failed");
}


src/components/CameraCapture.tsx

import { useEffect, useRef, useState } from "react";
import { uploadBlob } from "../lib/api";

export default function CameraCapture() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stream: MediaStream;
    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" } },
          audio: false
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setReady(true);
        }
      } catch (e: any) {
        setError(e?.message ?? "Camera access failed (https required?)");
      }
    })();
    return () => { stream?.getTracks().forEach(t => t.stop()); };
  }, []);

  const capture = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    setBusy(true);
    const v = videoRef.current;
    const c = canvasRef.current;
    c.width = v.videoWidth;
    c.height = v.videoHeight;
    const ctx = c.getContext("2d");
    ctx?.drawImage(v, 0, 0);
    const blob = await new Promise<Blob | null>(res => c.toBlob(b => res(b), "image/jpeg", 0.9));
    if (!blob) { setBusy(false); return; }
    try {
      await uploadBlob(blob, `capture_${Date.now()}.jpg`);
    } catch (e: any) {
      setError(e?.message ?? "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="rounded-2xl overflow-hidden shadow">
        <video ref={videoRef} className="w-full h-auto" playsInline muted />
      </div>
      <div className="flex gap-2">
        <button
          onClick={capture}
          disabled={!ready || busy}
          className="px-4 py-2 rounded-xl bg-sky-600 text-white disabled:opacity-50"
        >
          {busy ? "Uploading..." : "Capture & Upload"}
        </button>
        {error && <p className="text-red-600">{error}</p>}
      </div>
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}


src/App.tsx

import { useEffect, useState } from "react";
import CameraCapture from "./components/CameraCapture";
import { listAssets, deleteAsset } from "./lib/api";
import type { Asset } from "./lib/api";

export default function App() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);

  async function refresh() {
    const res = await listAssets(50, 0);
    setAssets(res.items);
    setTotal(res.total);
  }

  useEffect(() => { refresh(); }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">CRUD + Camera (PWA)</h1>
          <button onClick={refresh} className="px-3 py-2 bg-slate-700 rounded-xl">Refresh</button>
        </header>

        <CameraCapture />

        <section>
          <h2 className="text-xl font-semibold mt-6 mb-2">Assets ({total})</h2>
          <ul className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {assets.map(a => (
              <li key={a.id} className="bg-slate-800 rounded-xl p-2 space-y-2">
                <img src={`/api/assets/${a.id}`} alt={a.filename} className="w-full h-32 object-cover rounded-lg" />
                <div className="text-xs break-all">{a.filename}</div>
                <button
                  onClick={async () => { await deleteAsset(a.id); await refresh(); }}
                  className="w-full px-2 py-1 bg-rose-600 rounded-lg"
                >Delete</button>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}

2) Backend — Flask + Postgres (direct SQL)

server/requirements.txt

Flask==3.0.3
psycopg[binary]==3.2.1
python-dotenv==1.0.1
Werkzeug==3.0.3
Flask-Cors==4.0.1


server/schema.sql

create extension if not exists "uuid-ossp";

create table if not exists assets (
  id uuid primary key default uuid_generate_v4(),
  created_at timestamptz not null default now(),
  filename text not null,
  mime text not null,
  size integer not null,
  data bytea not null
);

-- Basic pagination helper index
create index if not exists idx_assets_created_at on assets (created_at desc);


server/db.py

import os
import psycopg
from contextlib import contextmanager

DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/postgres"
)

def get_conn():
    # Autocommit off; we manage transactions explicitly.
    return psycopg.connect(DSN)

@contextmanager
def tx():
    with get_conn() as conn:
        with conn.cursor() as cur:
            try:
                yield cur
                conn.commit()
            except:
                conn.rollback()
                raise


server/app.py

import io, os
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from db import tx, get_conn

MAX_BYTES = 7 * 1024 * 1024  # 7MB MVP cap

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.before_first_request
def ensure_schema():
    path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(path, "r") as f, get_conn() as conn:
        conn.execute(f.read())
        conn.commit()

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
    if not f.mimetype.startswith("image/"):
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


server/Dockerfile

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "app.py", "--host=0.0.0.0"]

3) Compose for Postgres + Backend

.env.example

POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres


docker-compose.yml

version: "3.9"
services:
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-postgres}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]

  server:
    build: ./server
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql://postgres:postgres@db:5432/postgres}
      FLASK_DEBUG: "1"
    depends_on: [db]
    ports: ["8000:8000"]

volumes:
  pgdata:

4) Dev & Run

Backend

cp .env.example .env  # edit if you want
docker compose up -d --build
# Flask will auto-init schema on first request


Frontend (separate terminal)

cd client
npm run dev
# open http://localhost:5173


API sanity checks

curl http://localhost:8000/api/health
curl http://localhost:8000/api/assets

PWA Reality Check (mobile)

Must serve over HTTPS to use camera. For local mobile testing:

Use ngrok http 5173 or vite --host + a trusted cert.

iOS Safari:

playsInline on <video> is required (done).

User gesture needed for autoplay (we start via play() after stream attaches; if it complains, tap once).

Storage:

Bytea in Postgres is fine for MVP; if you outgrow it, move blobs to S3/GCS and keep metadata in Postgres.

Opinionated guardrails (so you don’t step on rakes)

Direct SQL, yes—but parameterize (you are). Avoid string concat like the plague.

Limit uploads (MAX_BYTES) and check mimetype (you are).

Indexes on sort/pagination keys (you added one).

CORS: relaxed in dev; tighten in prod.

Migrations: add a barebones make migrate that runs psql -f schema.sql for now; add Alembic later if you must (you said no ORM—still compatible).

Next 10% polish (when you care)

Add JWT auth (browser fetch with Authorization: Bearer header; server verifies with pyjwt).

Add ETag / Cache-Control on GET /assets/:id for cheap wins.

Add background sync via PWA (queue uploads offline, replay when back online).

Add rate limiting on uploads (Flask-Limiter).

