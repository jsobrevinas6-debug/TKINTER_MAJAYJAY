import mysql.connector
from mysql.connector import Error, pooling

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "majayjay_db",
    "user":     "root",
    "password": "admin123",  # ← change this
}
# ── Connection pool (reuses connections, safer for threading) ──────────────────
_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="mjpool",
            pool_size=5,
            **DB_CONFIG
        )
    return _pool


def get_connection():
    """Get a connection from the pool."""
    return _get_pool().get_connection()


# ── Helper functions ───────────────────────────────────────────────────────────

def fetch_one(query: str, params: tuple = ()):
    """Run a SELECT and return a single row as a dict, or None."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchone()
    except Error as e:
        print(f"[DB ERROR] fetch_one: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def fetch_all(query: str, params: tuple = ()):
    """Run a SELECT and return all rows as a list of dicts."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] fetch_all: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def execute(query: str, params: tuple = ()):
    """Run INSERT / UPDATE / DELETE. Returns lastrowid or None."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"[DB ERROR] execute: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def test_connection():
    """Quick test — prints OK or the error."""
    try:
        conn = get_connection()
        if conn.is_connected():
            info = conn.server_info
            print(f"✅ Connected to MySQL Server version {info}")
            conn.close()
    except Error as e:
        print(f"❌ Connection failed: {e}")


# ── Auth helpers (replaces Supabase auth) ─────────────────────────────────────
import hashlib, os

def hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256."""
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        salt_hex, key_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return key.hex() == key_hex
    except Exception:
        return False


def login(email: str, password: str) -> dict | None:
    """
    Returns the user row dict if credentials are valid, else None.
    Raises ValueError with a message if something is wrong.
    """
    user = fetch_one(
        "SELECT * FROM users WHERE email = %s", (email,)
    )
    if not user:
        raise ValueError("No account found with that email.")
    if not verify_password(password, user["password"]):
        raise ValueError("Invalid email or password.")
    return user


def register_user(email: str, password: str, first_name: str,
                  middle_name: str, last_name: str,
                  user_type: str = "student") -> int | None:
    """
    Insert a new user. Returns the new user's ID or None on failure.
    Raises ValueError if email already exists.
    """
    existing = fetch_one(
        "SELECT user_id FROM users WHERE email = %s", (email,)
    )
    if existing:
        raise ValueError("This email is already registered.")

    hashed = hash_password(password)
    return execute(
        """
        INSERT INTO users (email, password, first_name, middle_name,
                           last_name, user_type)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (email, hashed, first_name, middle_name or None,
         last_name, user_type)
    )


# ── Run this file directly to test ────────────────────────────────────────────
if __name__ == "__main__":
    test_connection()