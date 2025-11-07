import sqlite3
from pathlib import Path
from typing import Optional, List, Any, Dict
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path("database/ev_stations.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ev_charging_stations_reduced (
  station_id TEXT PRIMARY KEY,
  name TEXT,
  operator TEXT,
  state TEXT,
  city TEXT,
  pincode TEXT,
  charger_types TEXT,
  number_of_chargers TEXT,
  power_kW_each TEXT,
  price_per_kWh_INR TEXT,
  tariff_type TEXT,
  payment_methods TEXT,
  opening_hours TEXT,
  contact_number TEXT,
  email TEXT,
  station_rating TEXT,
  num_reviews TEXT,
  parking_spaces TEXT,
  amenities TEXT,
  reservation_supported TEXT,
  fast_charging_supported TEXT,
  nearby_landmark TEXT,
  uptime_percent TEXT,
  status TEXT,
  latitude REAL,
  longitude REAL
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  station_id TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
  review_text TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (station_id) REFERENCES ev_charging_stations_reduced(station_id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS bookmarks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  station_id TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (station_id) REFERENCES ev_charging_stations_reduced(station_id),
  UNIQUE(user_id, station_id)
);

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  station_id TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  comment_text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (station_id) REFERENCES ev_charging_stations_reduced(station_id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS search_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  search_term TEXT,
  search_filters TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  station_id TEXT,
  message TEXT NOT NULL,
  is_read INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (station_id) REFERENCES ev_charging_stations_reduced(station_id)
);
"""


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def import_sql_file(sql_path: str):
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    with get_conn() as conn:
        conn.executescript(sql)
        conn.commit()


def list_distinct(column: str) -> List[str]:
    allowed = {
        'city', 'operator', 'status', 'tariff_type', 'fast_charging_supported'
    }
    if column not in allowed:
        return []
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT {column} FROM ev_charging_stations_reduced "
            f"WHERE {column} IS NOT NULL AND {column} <> '' ORDER BY {column}"
        ).fetchall()
    return [r[0] for r in rows]


def as_dataframe(
    city: Optional[str] = None,
    operator: Optional[str] = None,
    status: Optional[str] = None,
    fast: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
) -> pd.DataFrame:
    with get_conn() as conn:
        sql = "SELECT * FROM ev_charging_stations_reduced WHERE 1=1"
        params: List[Any] = []
        if city:
            sql += " AND city = ?"
            params.append(city)
        if operator:
            sql += " AND operator = ?"
            params.append(operator)
        if status:
            sql += " AND status = ?"
            params.append(status)
        if fast:
            sql += " AND fast_charging_supported = ?"
            params.append(fast)
        sql += " ORDER BY city, operator, name"
        df = pd.read_sql_query(sql, conn, params=params)

    # Apply numeric filters in pandas with coercion
    if (price_min is not None or price_max is not None) and (
        'price_per_kWh_INR' in df.columns
    ):
        prices = pd.to_numeric(df['price_per_kWh_INR'], errors='coerce')
        if price_min is not None:
            df = df[prices >= float(price_min)]
        if price_max is not None:
            df = df[prices <= float(price_max)]

    if (rating_min is not None or rating_max is not None) and (
        'station_rating' in df.columns
    ):
        ratings = pd.to_numeric(df['station_rating'], errors='coerce')
        if rating_min is not None:
            df = df[ratings >= float(rating_min)]
        if rating_max is not None:
            df = df[ratings <= float(rating_max)]
    return df


def upsert_station(row: Dict[str, Any]):
    cols = [
        'station_id', 'name', 'operator', 'state', 'city', 'pincode',
        'charger_types', 'number_of_chargers', 'power_kW_each',
        'price_per_kWh_INR', 'tariff_type', 'payment_methods', 'opening_hours',
        'contact_number', 'email', 'station_rating', 'num_reviews',
        'parking_spaces', 'amenities', 'reservation_supported',
        'fast_charging_supported', 'nearby_landmark', 'uptime_percent',
        'status'
    ]
    placeholders = ','.join(['?'] * len(cols))
    assignments = ','.join([
        f"{c}=excluded.{c}" for c in cols if c != 'station_id'
    ])
    values = [row.get(c) for c in cols]
    sql = (
        f"INSERT INTO ev_charging_stations_reduced ("
        f"{','.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT(station_id) DO UPDATE SET {assignments}"
    )
    with get_conn() as conn:
        conn.execute(sql, values)
        conn.commit()


def delete_station(station_id: str):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM ev_charging_stations_reduced WHERE station_id=?",
            (station_id,),
        )
        conn.commit()


# ==================== User Authentication Functions ====================

def create_user(name: str, email: str, password: str) -> Optional[int]:
    """Create a new user and return user ID, or None if email exists."""
    password_hash = generate_password_hash(password)
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Email already exists
        return None


def verify_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify user credentials and return user data if valid."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email,)
        )
        user = cursor.fetchone()
    
    if user and check_password_hash(user[3], password):
        return {
            'id': user[0],
            'name': user[1],
            'email': user[2]
        }
    return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE email = ?",
            (email,)
        )
        user = cursor.fetchone()
    
    if user:
        return {
            'id': user[0],
            'name': user[1],
            'email': user[2],
            'created_at': user[3]
        }
    return None


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users (for admin purposes)."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT id, name, email, created_at FROM users ORDER BY created_at DESC"
        )
        users = cursor.fetchall()
    
    return [
        {
            'id': user[0],
            'name': user[1],
            'email': user[2],
            'created_at': user[3]
        }
        for user in users
    ]


# ==================== Reviews & Ratings Functions ====================

def add_review(station_id: str, user_id: int, rating: int, review_text: str = "") -> Optional[int]:
    """Add a review for a station."""
    if rating < 1 or rating > 5:
        return None
    
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO reviews (station_id, user_id, rating, review_text) 
                   VALUES (?, ?, ?, ?)""",
                (station_id, user_id, rating, review_text)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception:
        return None


def get_station_reviews(station_id: str) -> List[Dict[str, Any]]:
    """Get all reviews for a station with user info."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT r.id, r.rating, r.review_text, r.created_at, 
                      u.name, u.email
               FROM reviews r
               JOIN users u ON r.user_id = u.id
               WHERE r.station_id = ?
               ORDER BY r.created_at DESC""",
            (station_id,)
        )
        reviews = cursor.fetchall()
    
    return [
        {
            'id': rev[0],
            'rating': rev[1],
            'review_text': rev[2],
            'created_at': rev[3],
            'user_name': rev[4],
            'user_email': rev[5]
        }
        for rev in reviews
    ]


def get_user_reviews(user_id: int) -> List[Dict[str, Any]]:
    """Get all reviews by a user."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT r.id, r.station_id, r.rating, r.review_text, r.created_at,
                      s.name as station_name
               FROM reviews r
               LEFT JOIN ev_charging_stations_reduced s ON r.station_id = s.station_id
               WHERE r.user_id = ?
               ORDER BY r.created_at DESC""",
            (user_id,)
        )
        reviews = cursor.fetchall()
    
    return [
        {
            'id': rev[0],
            'station_id': rev[1],
            'rating': rev[2],
            'review_text': rev[3],
            'created_at': rev[4],
            'station_name': rev[5]
        }
        for rev in reviews
    ]


def get_station_average_rating(station_id: str) -> Optional[float]:
    """Get average rating for a station."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT AVG(rating) FROM reviews WHERE station_id = ?",
            (station_id,)
        )
        result = cursor.fetchone()
    
    return round(result[0], 1) if result[0] else None


def search_stations_by_location(search_term: str) -> pd.DataFrame:
    """Search stations by city, state, or pincode."""
    with get_conn() as conn:
        sql = """
            SELECT * FROM ev_charging_stations_reduced 
            WHERE city LIKE ? OR state LIKE ? OR pincode LIKE ?
            ORDER BY city, name
        """
        search_pattern = f"%{search_term}%"
        df = pd.read_sql_query(
            sql, conn, params=(search_pattern, search_pattern, search_pattern)
        )
    return df


# ==================== Bookmarks Functions ====================

def add_bookmark(user_id: int, station_id: str) -> Optional[int]:
    """Bookmark a station for a user."""
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO bookmarks (user_id, station_id) VALUES (?, ?)",
                (user_id, station_id)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def remove_bookmark(user_id: int, station_id: str) -> bool:
    """Remove a bookmark."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM bookmarks WHERE user_id = ? AND station_id = ?",
            (user_id, station_id)
        )
        conn.commit()
    return True


def get_user_bookmarks(user_id: int) -> List[Dict[str, Any]]:
    """Get all bookmarked stations for a user."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT s.*, b.created_at as bookmarked_at
               FROM bookmarks b
               JOIN ev_charging_stations_reduced s ON b.station_id = s.station_id
               WHERE b.user_id = ?
               ORDER BY b.created_at DESC""",
            (user_id,)
        )
        stations = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, station)) for station in stations]


def is_bookmarked(user_id: int, station_id: str) -> bool:
    """Check if a station is bookmarked by user."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM bookmarks WHERE user_id = ? AND station_id = ?",
            (user_id, station_id)
        )
        return cursor.fetchone() is not None


# ==================== Comments Functions ====================

def add_comment(station_id: str, user_id: int, comment_text: str) -> Optional[int]:
    """Add a comment to a station."""
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO comments (station_id, user_id, comment_text) VALUES (?, ?, ?)",
                (station_id, user_id, comment_text)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception:
        return None


def get_station_comments(station_id: str) -> List[Dict[str, Any]]:
    """Get all comments for a station."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT c.id, c.comment_text, c.created_at, u.name, u.email
               FROM comments c
               JOIN users u ON c.user_id = u.id
               WHERE c.station_id = ?
               ORDER BY c.created_at DESC""",
            (station_id,)
        )
        comments = cursor.fetchall()
    
    return [
        {
            'id': com[0],
            'comment_text': com[1],
            'created_at': com[2],
            'user_name': com[3],
            'user_email': com[4]
        }
        for com in comments
    ]


# ==================== Search History Functions ====================

def save_search_history(user_id: int, search_term: str = "", filters: str = ""):
    """Save user's search history."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO search_history (user_id, search_term, search_filters) VALUES (?, ?, ?)",
            (user_id, search_term, filters)
        )
        conn.commit()


def get_recent_searches(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's recent searches."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT DISTINCT search_term, search_filters, created_at
               FROM search_history
               WHERE user_id = ? AND search_term != ''
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, limit)
        )
        searches = cursor.fetchall()
    
    return [
        {
            'search_term': s[0],
            'search_filters': s[1],
            'created_at': s[2]
        }
        for s in searches
    ]


# ==================== Notifications Functions ====================

def create_notification(user_id: int, message: str, station_id: str = None):
    """Create a notification for a user."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notifications (user_id, station_id, message) VALUES (?, ?, ?)",
            (user_id, station_id, message)
        )
        conn.commit()


def get_user_notifications(user_id: int, unread_only: bool = False) -> List[Dict[str, Any]]:
    """Get notifications for a user."""
    with get_conn() as conn:
        sql = "SELECT * FROM notifications WHERE user_id = ?"
        if unread_only:
            sql += " AND is_read = 0"
        sql += " ORDER BY created_at DESC LIMIT 20"
        
        cursor = conn.execute(sql, (user_id,))
        notifications = cursor.fetchall()
    
    return [
        {
            'id': n[0],
            'station_id': n[2],
            'message': n[3],
            'is_read': n[4],
            'created_at': n[5]
        }
        for n in notifications
    ]


def mark_notification_read(notification_id: int):
    """Mark a notification as read."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,)
        )
        conn.commit()


def get_unread_count(user_id: int) -> int:
    """Get count of unread notifications."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,)
        )
        result = cursor.fetchone()
    return result[0] if result else 0


# ==================== Wallet Functions ====================

def get_or_create_wallet(user_id: int) -> Dict[str, Any]:
    """Get user's wallet or create if doesn't exist."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM wallets WHERE user_id = ?",
            (user_id,)
        )
        wallet = cursor.fetchone()
        
        if not wallet:
            conn.execute(
                "INSERT INTO wallets (user_id, balance) VALUES (?, 0.0)",
                (user_id,)
            )
            conn.commit()
            return {'user_id': user_id, 'balance': 0.0}
        
        return {
            'id': wallet[0],
            'user_id': wallet[1],
            'balance': wallet[2],
            'updated_at': wallet[3]
        }


def get_wallet_balance(user_id: int) -> float:
    """Get user's wallet balance."""
    wallet = get_or_create_wallet(user_id)
    return wallet['balance']


def add_to_wallet(user_id: int, amount: float, description: str = ""):
    """Add money to user's wallet."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE wallets SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (amount, user_id)
        )
        conn.execute(
            "INSERT INTO wallet_transactions (user_id, amount, transaction_type, description) VALUES (?, ?, 'credit', ?)",
            (user_id, amount, description)
        )
        conn.commit()


def deduct_from_wallet(user_id: int, amount: float, description: str = "", booking_id: int = None):
    """Deduct money from user's wallet."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT balance FROM wallets WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result or result[0] < amount:
            return False
        
        conn.execute(
            "UPDATE wallets SET balance = balance - ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (amount, user_id)
        )
        conn.execute(
            "INSERT INTO wallet_transactions (user_id, amount, transaction_type, description, booking_id) VALUES (?, ?, 'debit', ?, ?)",
            (user_id, -amount, description, booking_id)
        )
        conn.commit()
        return True


def get_wallet_transactions(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Get user's wallet transaction history."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        transactions = cursor.fetchall()
    
    return [
        {
            'id': t[0],
            'amount': t[2],
            'transaction_type': t[3],
            'description': t[4],
            'booking_id': t[5],
            'created_at': t[6]
        }
        for t in transactions
    ]


# ==================== Payment Request Functions ====================

def create_payment_request(user_id: int, amount: float, transaction_id: str = "", payment_method: str = "") -> int:
    """Create a payment request for admin verification."""
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO payment_requests (user_id, amount, transaction_id, payment_method, status) VALUES (?, ?, ?, ?, 'pending')",
            (user_id, amount, transaction_id, payment_method)
        )
        conn.commit()
        return cursor.lastrowid


def get_pending_payment_requests() -> List[Dict[str, Any]]:
    """Get all pending payment requests for admin."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT pr.*, u.name, u.email 
               FROM payment_requests pr
               JOIN users u ON pr.user_id = u.id
               WHERE pr.status = 'pending'
               ORDER BY pr.created_at DESC"""
        )
        requests = cursor.fetchall()
    
    return [
        {
            'id': r[0],
            'user_id': r[1],
            'amount': r[2],
            'transaction_id': r[3],
            'payment_method': r[4],
            'status': r[5],
            'created_at': r[7],
            'user_name': r[9],
            'user_email': r[10]
        }
        for r in requests
    ]


def get_all_payment_requests() -> List[Dict[str, Any]]:
    """Get all payment requests for admin."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT pr.*, u.name, u.email 
               FROM payment_requests pr
               JOIN users u ON pr.user_id = u.id
               ORDER BY pr.created_at DESC"""
        )
        requests = cursor.fetchall()
    
    return [
        {
            'id': r[0],
            'user_id': r[1],
            'amount': r[2],
            'transaction_id': r[3],
            'payment_method': r[4],
            'status': r[5],
            'admin_notes': r[6],
            'created_at': r[7],
            'verified_at': r[8],
            'user_name': r[9],
            'user_email': r[10]
        }
        for r in requests
    ]


def approve_payment_request(request_id: int, admin_notes: str = "") -> bool:
    """Approve payment request and add money to user wallet."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT user_id, amount FROM payment_requests WHERE id = ?",
            (request_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False
        
        user_id, amount = result
        
        conn.execute(
            "UPDATE payment_requests SET status = 'approved', admin_notes = ?, verified_at = CURRENT_TIMESTAMP WHERE id = ?",
            (admin_notes, request_id)
        )
        conn.commit()
    
    add_to_wallet(user_id, amount, f"Payment approved - Request #{request_id}")
    create_notification(user_id, f"Your payment of ₹{amount} has been approved and added to your wallet!")
    
    return True


def reject_payment_request(request_id: int, admin_notes: str = "") -> bool:
    """Reject payment request."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT user_id, amount FROM payment_requests WHERE id = ?",
            (request_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False
        
        user_id, amount = result
        
        conn.execute(
            "UPDATE payment_requests SET status = 'rejected', admin_notes = ?, verified_at = CURRENT_TIMESTAMP WHERE id = ?",
            (admin_notes, request_id)
        )
        conn.commit()
    
    create_notification(user_id, f"Your payment request of ₹{amount} was rejected. Reason: {admin_notes}")
    
    return True


def get_user_payment_requests(user_id: int) -> List[Dict[str, Any]]:
    """Get payment requests for a specific user."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM payment_requests WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        requests = cursor.fetchall()
    
    return [
        {
            'id': r[0],
            'amount': r[2],
            'transaction_id': r[3],
            'payment_method': r[4],
            'status': r[5],
            'admin_notes': r[6],
            'created_at': r[7],
            'verified_at': r[8]
        }
        for r in requests
    ]


# ==================== Booking Functions ====================

def create_booking(user_id: int, station_id: str, booking_date: str, 
                   booking_time: str, duration_hours: float, total_amount: float) -> Optional[int]:
    """Create a new booking."""
    balance = get_wallet_balance(user_id)
    
    if balance < total_amount:
        return None
    
    with get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO bookings 
               (user_id, station_id, booking_date, booking_time, 
                duration_hours, total_amount, payment_status, booking_status) 
               VALUES (?, ?, ?, ?, ?, ?, 'paid', 'confirmed')""",
            (user_id, station_id, booking_date, booking_time, 
             duration_hours, total_amount)
        )
        booking_id = cursor.lastrowid
        conn.commit()
    
    deduct_from_wallet(user_id, total_amount, f"Booking for station {station_id} on {booking_date} at {booking_time}", booking_id)
    create_notification(user_id, f"Booking confirmed! Station booked for {booking_date} at {booking_time}", station_id)
    
    return booking_id


def get_user_bookings(user_id: int) -> List[Dict[str, Any]]:
    """Get all bookings for a user (only upcoming and today's bookings)."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT b.*, s.name, s.city, s.state, s.nearby_landmark 
               FROM bookings b
               JOIN ev_charging_stations_reduced s ON b.station_id = s.station_id
               WHERE b.user_id = ? 
               AND b.booking_status = 'confirmed'
               AND (b.booking_date > date('now') 
                    OR (b.booking_date = date('now') AND b.booking_time >= time('now')))
               ORDER BY b.booking_date ASC, b.booking_time ASC""",
            (user_id,)
        )
        bookings = cursor.fetchall()
    
    return [
        {
            'id': b[0],
            'station_id': b[2],
            'booking_date': b[3],
            'booking_time': b[4],
            'duration_hours': b[5],
            'total_amount': b[6],
            'payment_status': b[7],
            'booking_status': b[8],
            'created_at': b[9],
            'station_name': b[10],
            'city': b[11],
            'state': b[12],
            'landmark': b[13]
        }
        for b in bookings
    ]


def get_user_charging_history(user_id: int) -> Dict[str, Any]:
    """Get past charging history for a user with total spending."""
    with get_conn() as conn:
        # Get past completed bookings
        cursor = conn.execute(
            """SELECT b.*, s.name, s.city, s.state, s.nearby_landmark 
               FROM bookings b
               JOIN ev_charging_stations_reduced s ON b.station_id = s.station_id
               WHERE b.user_id = ? 
               AND b.booking_status = 'confirmed'
               AND (b.booking_date < date('now') 
                    OR (b.booking_date = date('now') AND b.booking_time < time('now')))
               ORDER BY b.booking_date DESC, b.booking_time DESC""",
            (user_id,)
        )
        bookings = cursor.fetchall()
        
        # Calculate total spending
        cursor = conn.execute(
            """SELECT 
                 COUNT(*) as total_sessions,
                 SUM(total_amount) as total_spent,
                 SUM(duration_hours) as total_hours
               FROM bookings 
               WHERE user_id = ? 
               AND booking_status = 'confirmed'
               AND (booking_date < date('now') 
                    OR (booking_date = date('now') AND booking_time < time('now')))""",
            (user_id,)
        )
        stats = cursor.fetchone()
    
    history_list = [
        {
            'id': b[0],
            'station_id': b[2],
            'booking_date': b[3],
            'booking_time': b[4],
            'duration_hours': b[5],
            'total_amount': b[6],
            'payment_status': b[7],
            'booking_status': b[8],
            'created_at': b[9],
            'station_name': b[10],
            'city': b[11],
            'state': b[12],
            'landmark': b[13]
        }
        for b in bookings
    ]
    
    return {
        'history': history_list,
        'total_sessions': stats[0] if stats else 0,
        'total_spent': stats[1] if stats and stats[1] else 0.0,
        'total_hours': stats[2] if stats and stats[2] else 0.0
    }


def get_all_bookings() -> List[Dict[str, Any]]:
    """Get all bookings for admin."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT b.*, s.name, s.city, s.state, u.name, u.email 
               FROM bookings b
               JOIN ev_charging_stations_reduced s ON b.station_id = s.station_id
               JOIN users u ON b.user_id = u.id
               ORDER BY b.created_at DESC"""
        )
        bookings = cursor.fetchall()
    
    return [
        {
            'id': b[0],
            'user_id': b[1],
            'station_id': b[2],
            'booking_date': b[3],
            'booking_time': b[4],
            'duration_hours': b[5],
            'total_amount': b[6],
            'payment_status': b[7],
            'booking_status': b[8],
            'created_at': b[9],
            'station_name': b[10],
            'city': b[11],
            'state': b[12],
            'user_name': b[13],
            'user_email': b[14]
        }
        for b in bookings
    ]


def cancel_booking(booking_id: int, user_id: int) -> bool:
    """Cancel a booking and refund to wallet."""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT total_amount, booking_status FROM bookings WHERE id = ? AND user_id = ?",
            (booking_id, user_id)
        )
        result = cursor.fetchone()
        
        if not result or result[1] == 'cancelled':
            return False
        
        total_amount = result[0]
        
        conn.execute(
            "UPDATE bookings SET booking_status = 'cancelled' WHERE id = ?",
            (booking_id,)
        )
        conn.commit()
    
    add_to_wallet(user_id, total_amount, f"Refund for cancelled booking #{booking_id}")
    create_notification(user_id, f"Booking #{booking_id} cancelled. ₹{total_amount} refunded to your wallet.")
    
    return True


