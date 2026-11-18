import os
import time

import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD"),
    )


def init_db():
    # The database may still be starting, so retry for up to 30 seconds
    for attempt in range(30):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS notes ("
                    "id SERIAL PRIMARY KEY, "
                    "text TEXT NOT NULL, "
                    "created_at TIMESTAMP DEFAULT now())"
                )
            print("Database ready", flush=True)
            return
        except psycopg2.OperationalError as e:
            print(f"Waiting for database ({attempt + 1}/30): {e}", flush=True)
            time.sleep(1)
    raise RuntimeError("Database never became available")


init_db()


@app.route("/api/health")
def health():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify(status="ok"), 200
    except Exception:
        return jsonify(status="database unavailable"), 503


@app.route("/api/notes", methods=["GET"])
def list_notes():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, text FROM notes ORDER BY id")
        rows = cur.fetchall()
    return jsonify([{"id": r[0], "text": r[1]} for r in rows])


@app.route("/api/notes", methods=["POST"])
def add_note():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify(error="text is required"), 400
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO notes (text) VALUES (%s) RETURNING id", (text,))
        note_id = cur.fetchone()[0]
    return jsonify(id=note_id, text=text), 201
