import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea todas las tablas si no existen."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_keys (
                user_id     INTEGER PRIMARY KEY,
                quantity    INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS giveaways (
                message_id      INTEGER PRIMARY KEY,
                channel_id      INTEGER NOT NULL,
                guild_id        INTEGER NOT NULL,
                prize           TEXT NOT NULL,
                description     TEXT NOT NULL,
                host_id         INTEGER NOT NULL,
                start_time      TEXT NOT NULL,
                active          INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS giveaway_entries (
                giveaway_id     INTEGER NOT NULL,
                user_id         INTEGER NOT NULL,
                PRIMARY KEY (giveaway_id, user_id),
                FOREIGN KEY (giveaway_id) REFERENCES giveaways(message_id)
            );

            CREATE TABLE IF NOT EXISTS mystery_boxes (
                message_id      INTEGER PRIMARY KEY,
                channel_id      INTEGER NOT NULL,
                guild_id        INTEGER NOT NULL,
                prize           TEXT NOT NULL,
                prize_method    TEXT NOT NULL,
                host_id         INTEGER NOT NULL,
                start_time      TEXT NOT NULL,
                active          INTEGER NOT NULL DEFAULT 1,
                pending_user_id INTEGER DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS key_giveaways (
                message_id      INTEGER PRIMARY KEY,
                host_id         INTEGER NOT NULL,
                active          INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                type            TEXT NOT NULL,
                event_time      TEXT NOT NULL,
                data            TEXT NOT NULL
            );
        """)
    print("✅ Base de datos iniciada correctamente.")


# ─────────────────────────────────────────────
#  LLAVES
# ─────────────────────────────────────────────

def get_keys(user_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT quantity FROM user_keys WHERE user_id = ?", (user_id,)).fetchone()
        return row["quantity"] if row else 0


def add_keys(user_id: int, amount: int):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO user_keys (user_id, quantity) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET quantity = quantity + excluded.quantity
        """, (user_id, amount))


def remove_keys(user_id: int, amount: int):
    current = get_keys(user_id)
    new_qty = max(0, current - amount)
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO user_keys (user_id, quantity) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET quantity = excluded.quantity
        """, (user_id, new_qty))
    return new_qty


# ─────────────────────────────────────────────
#  GIVEAWAYS
# ─────────────────────────────────────────────

def create_giveaway(message_id, channel_id, guild_id, prize, description, host_id, start_time):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO giveaways (message_id, channel_id, guild_id, prize, description, host_id, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (message_id, channel_id, guild_id, prize, description, host_id, start_time))


def add_giveaway_entry(giveaway_id: int, user_id: int) -> bool:
    """Devuelve True si se añadió, False si ya estaba inscrito."""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO giveaway_entries (giveaway_id, user_id) VALUES (?, ?)",
                (giveaway_id, user_id)
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_giveaway_entries(giveaway_id: int) -> list[int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?", (giveaway_id,)
        ).fetchall()
        return [r["user_id"] for r in rows]


def get_giveaway_entry_count(giveaway_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM giveaway_entries WHERE giveaway_id = ?", (giveaway_id,)
        ).fetchone()
        return row["cnt"]

def remove_giveaway_entry(giveaway_id: int, user_id: int) -> bool:
    """Elimina un participante del giveaway. Devuelve True si existía.""\"
    with get_conn() as conn:
        cursor = conn.execute(
            "DELETE FROM giveaway_entries WHERE giveaway_id = ? AND user_id = ?",
            (giveaway_id, user_id)
        )
        return cursor.rowcount > 0


def get_giveaway(message_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM giveaways WHERE message_id = ? AND active = 1", (message_id,)
        ).fetchone()


def close_giveaway(message_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE giveaways SET active = 0 WHERE message_id = ?", (message_id,))


def get_active_giveaways(guild_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM giveaways WHERE guild_id = ? AND active = 1", (guild_id,)
        ).fetchall()


# ─────────────────────────────────────────────
#  MYSTERY BOXES
# ─────────────────────────────────────────────

def create_mystery_box(message_id, channel_id, guild_id, prize, prize_method, host_id, start_time):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO mystery_boxes (message_id, channel_id, guild_id, prize, prize_method, host_id, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (message_id, channel_id, guild_id, prize, prize_method, host_id, start_time))


def get_mystery_box(message_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM mystery_boxes WHERE message_id = ? AND active = 1", (message_id,)
        ).fetchone()


def set_box_pending_user(message_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE mystery_boxes SET pending_user_id = ? WHERE message_id = ?",
            (user_id, message_id)
        )


def clear_box_pending_user(message_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE mystery_boxes SET pending_user_id = NULL WHERE message_id = ?", (message_id,)
        )


def close_mystery_box(message_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE mystery_boxes SET active = 0 WHERE message_id = ?", (message_id,))


# ─────────────────────────────────────────────
#  KEY GIVEAWAYS
# ─────────────────────────────────────────────

def create_key_giveaway(message_id: int, host_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO key_giveaways (message_id, host_id) VALUES (?, ?)",
            (message_id, host_id)
        )


def close_key_giveaway(message_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE key_giveaways SET active = 0 WHERE message_id = ?", (message_id,))


def get_key_giveaway(message_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM key_giveaways WHERE message_id = ? AND active = 1", (message_id,)
        ).fetchone()


# ─────────────────────────────────────────────
#  HISTORIAL
# ─────────────────────────────────────────────

def log_event(event_type: str, data: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO history (type, event_time, data) VALUES (?, ?, ?)",
            (event_type, datetime.now().strftime("%d/%m/%Y %H:%M"), json.dumps(data))
        )
