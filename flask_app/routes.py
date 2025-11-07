import os
import flask as f
from app_db import (
    as_dataframe, list_distinct, upsert_station, delete_station,
    create_user, verify_user, get_user_by_email, get_all_users,
    add_review, get_station_reviews, get_user_reviews,
    get_station_average_rating, search_stations_by_location,
    add_bookmark, remove_bookmark, get_user_bookmarks, is_bookmarked,
    add_comment, get_station_comments,
    save_search_history, get_recent_searches,
    create_notification, get_user_notifications, mark_notification_read,
    get_unread_count,
    get_or_create_wallet, get_wallet_balance, get_wallet_transactions,
    create_payment_request, get_pending_payment_requests,
    get_all_payment_requests, approve_payment_request, reject_payment_request,
    get_user_payment_requests,
    create_booking, get_user_bookings, get_all_bookings, cancel_booking
)


bp = f.Blueprint("main", __name__)


@bp.route("/landing")
def landing():
    return f.render_template("landing.html")


@bp.route("/user/login", methods=["GET", "POST"])
def user_login():
    if f.request.method == "POST":
        email = f.request.form.get("email", "").strip()
        pwd = f.request.form.get("password", "").strip()
        
        if not email or not pwd:
            f.flash("Email and password required", "danger")
            return f.render_template("user_login.html")
        
        user = verify_user(email, pwd)
        if user:
            f.session["user_id"] = user["id"]
            f.session["user_email"] = user["email"]
            f.session["user_name"] = user["name"]
            f.flash(f"Welcome back, {user['name']}!", "success")
            return f.redirect(f.url_for("main.index"))
        
        f.flash("Invalid email or password", "danger")
    return f.render_template("user_login.html")


@bp.route("/user/signup", methods=["GET", "POST"])
def user_signup():
    if f.request.method == "POST":
        form = f.request.form
        name = form.get("name", "").strip()
        email = form.get("email", "").strip()
        pwd = form.get("password", "").strip()
        pwd2 = form.get("password_confirm", "").strip()

        if not (name and email and pwd and pwd2):
            f.flash("All fields are required", "danger")
            return f.render_template(
                "user_signup.html", name=name, email=email
            )
        if len(pwd) < 6:
            f.flash("Password must be at least 6 characters", "danger")
            return f.render_template(
                "user_signup.html", name=name, email=email
            )
        if pwd != pwd2:
            f.flash("Passwords do not match", "danger")
            return f.render_template(
                "user_signup.html", name=name, email=email
            )

        # Create user in database
        user_id = create_user(name, email, pwd)
        if user_id:
            f.session["user_id"] = user_id
            f.session["user_email"] = email
            f.session["user_name"] = name
            f.flash(f"Account created successfully! Welcome, {name}!", "success")
            return f.redirect(f.url_for("main.index"))
        else:
            f.flash("Email already exists. Please login instead.", "danger")
            return f.render_template(
                "user_signup.html", name=name, email=email
            )

    return f.render_template("user_signup.html")


@bp.route("/user/logout")
def user_logout():
    f.session.pop("user_id", None)
    f.session.pop("user_email", None)
    f.session.pop("user_name", None)
    f.flash("Logged out successfully", "info")
    return f.redirect(f.url_for("main.landing"))


@bp.route("/")
def home():
    """Redirect to landing page."""
    return f.redirect(f.url_for("main.landing"))


@bp.route("/stations")
def index():
    # Location search parameter
    location = f.request.args.get("location", "").strip()
    
    city = f.request.args.get("city") or None
    operator = f.request.args.get("operator") or None
    status = f.request.args.get("status") or None
    fast = f.request.args.get("fast") or None
    price_min = f.request.args.get("price_min")
    price_max = f.request.args.get("price_max")
    rating_min = f.request.args.get("rating_min")
    rating_max = f.request.args.get("rating_max")

    def _to_float(v):
        try:
            return float(v) if v not in (None, "") else None
        except Exception:
            return None
    
    # Use location search if provided, otherwise use filters
    if location:
        df = search_stations_by_location(location)
        f.flash(f"Showing results for location: {location}", "info")
    else:
        df = as_dataframe(
            city, operator, status, fast,
            price_min=_to_float(price_min), price_max=_to_float(price_max),
            rating_min=_to_float(rating_min), rating_max=_to_float(rating_max)
        )

    cities = list_distinct("city")
    operators = list_distinct("operator")
    statuses = list_distinct("status")
    fast_opts = list_distinct("fast_charging_supported")
    return f.render_template(
        "index.html",
        df=df,
        cities=cities,
        operators=operators,
        statuses=statuses,
        fast_opts=fast_opts,
        selected_city=city,
        selected_operator=operator,
        selected_status=status,
        selected_fast=fast,
        price_min=price_min or "",
        price_max=price_max or "",
        rating_min=rating_min or "",
        rating_max=rating_max or "",
        location=location
    )
    return f.render_template(
        "index.html",
        df=df,
        cities=cities,
        operators=operators,
        statuses=statuses,
        fast_opts=fast_opts,
        selected_city=city,
        selected_operator=operator,
        selected_status=status,
        selected_fast=fast,
        price_min=price_min or "",
        price_max=price_max or "",
        rating_min=rating_min or "",
        rating_max=rating_max or "",
    )


@bp.route("/analytics")
def analytics():
    df = as_dataframe()
    records = df.to_dict(orient="records")
    return f.render_template("analytics.html", rows=records)


@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if f.request.method == "POST":
        pwd = f.request.form.get("password", "")
        expected = os.environ.get("EV_ADMIN_PASSWORD", "admin")
        if pwd == expected:
            f.session["is_admin"] = True
            f.flash("Admin logged in", "success")
            return f.redirect(f.url_for("main.admin_stations"))
        f.flash("Invalid password", "danger")
    return f.render_template("admin_login.html")


@bp.route("/admin/logout")
def admin_logout():
    f.session.pop("is_admin", None)
    f.flash("Logged out", "info")
    return f.redirect(f.url_for("main.landing"))


def require_admin():
    if not f.session.get("is_admin"):
        f.flash("Admin login required", "warning")
        return False
    return True


@bp.route("/admin/stations", methods=["GET", "POST"])
def admin_stations():
    if not require_admin():
        return f.redirect(f.url_for("main.admin_login"))

    if f.request.method == "POST":
        form = f.request.form
        station_id = form.get("station_id", "").strip()
        if not station_id:
            f.flash("Station ID is required", "danger")
            return f.redirect(f.url_for("main.admin_stations"))
        try:
            payload = {
                "station_id": station_id,
                "name": form.get("name", ""),
                "operator": form.get("operator", ""),
                "state": form.get("state", ""),
                "city": form.get("city", ""),
                "pincode": form.get("pincode", ""),
                "charger_types": form.get("charger_types", ""),
                "number_of_chargers": int(
                    form.get("number_of_chargers", 0) or 0
                ),
                "power_kW_each": form.get("power_kW_each", ""),
                "price_per_kWh_INR": float(
                    form.get("price_per_kWh_INR", 0) or 0
                ),
                "tariff_type": form.get("tariff_type", ""),
                "payment_methods": form.get("payment_methods", ""),
                "opening_hours": form.get("opening_hours", ""),
                "contact_number": form.get("contact_number", ""),
                "email": form.get("email", ""),
                "station_rating": float(
                    form.get("station_rating", 0) or 0
                ),
                "num_reviews": int(form.get("num_reviews", 0) or 0),
                "parking_spaces": int(
                    form.get("parking_spaces", 0) or 0
                ),
                "amenities": form.get("amenities", ""),
                "reservation_supported": form.get(
                    "reservation_supported", "Unknown"
                ),
                "fast_charging_supported": form.get(
                    "fast_charging_supported", "Unknown"
                ),
                "nearby_landmark": form.get("nearby_landmark", ""),
                "uptime_percent": float(
                    form.get("uptime_percent", 0) or 0
                ),
                "status": form.get("status", "Active"),
            }
            upsert_station(payload)
            f.flash(f"Saved station {station_id}", "success")
        except Exception as e:
            f.flash(f"Save failed: {e}", "danger")
        return f.redirect(f.url_for("main.admin_stations"))

    df = as_dataframe()
    return f.render_template("admin_stations.html", df=df)


@bp.route("/admin/stations/delete", methods=["POST"])
def admin_delete_station():
    if not require_admin():
        return f.redirect(f.url_for("main.admin_login"))
    del_id = f.request.form.get("station_id")
    if not del_id:
        f.flash("Station ID required", "danger")
        return f.redirect(f.url_for("main.admin_stations"))
    try:
        delete_station(del_id)
        f.flash(f"Deleted station {del_id}", "success")
    except Exception as e:
        f.flash(f"Delete failed: {e}", "danger")
    return f.redirect(f.url_for("main.admin_stations"))


@bp.route("/station/<station_id>")
def station_detail(station_id: str):
    df = as_dataframe()
    row = None
    for r in df.to_dict(orient="records"):
        if r.get("station_id") == station_id:
            row = r
            break
    if not row:
        f.flash("Station not found", "warning")
        return f.redirect(f.url_for("main.index"))
    
    # Get reviews and comments for this station
    reviews = get_station_reviews(station_id)
    comments = get_station_comments(station_id)
    avg_rating = get_station_average_rating(station_id)
    
    # Check if bookmarked (for logged-in users)
    bookmarked = False
    if f.session.get("user_id"):
        bookmarked = is_bookmarked(f.session.get("user_id"), station_id)
    
    return f.render_template(
        "station_detail.html",
        row=row,
        reviews=reviews,
        comments=comments,
        avg_rating=avg_rating,
        bookmarked=bookmarked
    )


@bp.route("/station/<station_id>/review", methods=["POST"])
def add_station_review(station_id: str):
    """Add a review to a station."""
    if not f.session.get("user_id"):
        f.flash("Please login to add a review", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    rating = f.request.form.get("rating")
    review_text = f.request.form.get("review_text", "").strip()
    
    if not rating:
        f.flash("Please select a rating", "danger")
        return f.redirect(f.url_for("main.station_detail", station_id=station_id))
    
    try:
        rating_val = int(rating)
        review_id = add_review(station_id, user_id, rating_val, review_text)
        if review_id:
            f.flash("Review added successfully!", "success")
        else:
            f.flash("Failed to add review", "danger")
    except Exception as e:
        f.flash(f"Error: {e}", "danger")
    
    return f.redirect(f.url_for("main.station_detail", station_id=station_id))


@bp.route("/user/reviews")
def user_reviews():
    """Show all reviews by the logged-in user."""
    if not f.session.get("user_id"):
        f.flash("Please login to view your reviews", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    reviews = get_user_reviews(user_id)
    
    return f.render_template("user_reviews.html", reviews=reviews)


@bp.route("/bookmark/add/<station_id>", methods=["POST"])
def bookmark_station(station_id: str):
    """Add a station to bookmarks."""
    if not f.session.get("user_id"):
        f.flash("Please login to bookmark stations", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    result = add_bookmark(user_id, station_id)
    if result:
        f.flash("Station bookmarked!", "success")
        create_notification(user_id, f"You bookmarked a station", station_id)
    else:
        f.flash("Already bookmarked", "info")
    
    return f.redirect(f.url_for("main.station_detail", station_id=station_id))


@bp.route("/bookmark/remove/<station_id>", methods=["POST"])
def unbookmark_station(station_id: str):
    """Remove a station from bookmarks."""
    if not f.session.get("user_id"):
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    remove_bookmark(user_id, station_id)
    f.flash("Bookmark removed", "info")
    
    return f.redirect(f.url_for("main.station_detail", station_id=station_id))


@bp.route("/user/bookmarks")
def user_bookmarks():
    """Show user's bookmarked stations."""
    if not f.session.get("user_id"):
        f.flash("Please login to view bookmarks", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    bookmarks = get_user_bookmarks(user_id)
    
    return f.render_template("user_bookmarks.html", bookmarks=bookmarks)


@bp.route("/station/<station_id>/comment", methods=["POST"])
def add_station_comment(station_id: str):
    """Add a comment to a station."""
    if not f.session.get("user_id"):
        f.flash("Please login to comment", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    comment_text = f.request.form.get("comment_text", "").strip()
    
    if not comment_text:
        f.flash("Comment cannot be empty", "danger")
        return f.redirect(f.url_for("main.station_detail", station_id=station_id))
    
    comment_id = add_comment(station_id, user_id, comment_text)
    if comment_id:
        f.flash("Comment added!", "success")
    else:
        f.flash("Failed to add comment", "danger")
    
    return f.redirect(f.url_for("main.station_detail", station_id=station_id))


@bp.route("/user/dashboard")
def user_dashboard():
    """User personal dashboard."""
    if not f.session.get("user_id"):
        f.flash("Please login to view dashboard", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    
    # Get user stats
    bookmarks = get_user_bookmarks(user_id)
    reviews = get_user_reviews(user_id)
    recent_searches = get_recent_searches(user_id, 5)
    notifications = get_user_notifications(user_id, unread_only=False)
    unread_count = get_unread_count(user_id)
    bookings = get_user_bookings(user_id)
    wallet_balance = get_wallet_balance(user_id)
    
    return f.render_template(
        "user_dashboard.html",
        bookmarks=bookmarks,
        reviews=reviews,
        recent_searches=recent_searches,
        notifications=notifications,
        unread_count=unread_count,
        bookings=bookings,
        wallet_balance=wallet_balance
    )


@bp.route("/user/notifications")
def user_notifications_page():
    """Show all user notifications."""
    if not f.session.get("user_id"):
        f.flash("Please login", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    notifications = get_user_notifications(user_id, unread_only=False)
    
    return f.render_template("user_notifications.html", notifications=notifications)


@bp.route("/notification/read/<int:notification_id>", methods=["POST"])
def mark_read(notification_id: int):
    """Mark notification as read."""
    if not f.session.get("user_id"):
        return f.redirect(f.url_for("main.user_login"))
    
    mark_notification_read(notification_id)
    return f.redirect(f.url_for("main.user_notifications_page"))


@bp.route("/admin/users")
def admin_users():
    """View all registered users (admin only)."""
    if not require_admin():
        return f.redirect(f.url_for("main.admin_login"))
    users = get_all_users()
    return f.render_template("admin_users.html", users=users)


# ==================== Wallet & Payment Routes ====================

@bp.route("/wallet")
def user_wallet():
    """Show user wallet and transaction history."""
    if not f.session.get("user_id"):
        f.flash("Please login", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    wallet = get_or_create_wallet(user_id)
    transactions = get_wallet_transactions(user_id)
    payment_requests = get_user_payment_requests(user_id)
    
    return f.render_template("user_wallet.html", 
                           wallet=wallet, 
                           transactions=transactions,
                           payment_requests=payment_requests)


@bp.route("/wallet/add-money", methods=["POST"])
def add_money_request():
    """Submit payment request to admin."""
    if not f.session.get("user_id"):
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    amount = float(f.request.form.get("amount", 0))
    transaction_id = f.request.form.get("transaction_id", "").strip()
    payment_method = f.request.form.get("payment_method", "").strip()
    
    if amount <= 0:
        f.flash("Please enter a valid amount", "danger")
        return f.redirect(f.url_for("main.user_wallet"))
    
    create_payment_request(user_id, amount, transaction_id, payment_method)
    f.flash("Payment request submitted!", "success")
    
    return f.redirect(f.url_for("main.user_wallet"))


@bp.route("/admin/payments")
def admin_payments():
    """View all payment requests (admin only)."""
    if not require_admin():
        return f.redirect(f.url_for("main.admin_login"))
    
    pending_requests = get_pending_payment_requests()
    all_requests = get_all_payment_requests()
    
    return f.render_template("admin_payments.html", 
                           pending_requests=pending_requests,
                           all_requests=all_requests)


@bp.route("/admin/payment/approve/<int:request_id>", methods=["POST"])
def admin_approve_payment(request_id: int):
    """Approve payment request."""
    if not require_admin():
        return f.redirect(f.url_for("main.admin_login"))
    
    admin_notes = f.request.form.get("admin_notes", "").strip()
    
    if approve_payment_request(request_id, admin_notes):
        f.flash("Payment approved and added to user wallet!", "success")
    else:
        f.flash("Failed to approve payment", "danger")
    
    return f.redirect(f.url_for("main.admin_payments"))


@bp.route("/admin/payment/reject/<int:request_id>", methods=["POST"])
def admin_reject_payment(request_id: int):
    """Reject payment request."""
    if not require_admin():
        return f.redirect(f.url_for("main.admin_login"))
    
    admin_notes = f.request.form.get("admin_notes", "Rejected").strip()
    
    if reject_payment_request(request_id, admin_notes):
        f.flash("Payment request rejected", "info")
    else:
        f.flash("Failed to reject payment", "danger")
    
    return f.redirect(f.url_for("main.admin_payments"))


# ==================== Booking Routes ====================

@bp.route("/station/<station_id>/book", methods=["GET", "POST"])
def book_station(station_id: str):
    """Book a charging station."""
    if not f.session.get("user_id"):
        f.flash("Please login to book a station", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    
    if f.request.method == "POST":
        booking_date = f.request.form.get("booking_date")
        booking_time = f.request.form.get("booking_time")
        duration = float(f.request.form.get("duration", 1))
        charger_power = float(f.request.form.get("charger_power", 0))
        
        if charger_power <= 0:
            f.flash("Please select a charger power", "warning")
            return f.redirect(f.url_for("main.book_station", station_id=station_id))
        
        # Get station details to calculate price
        df = as_dataframe()
        station = df[df['station_id'] == station_id].iloc[0] if len(df) > 0 else None
        
        if station is not None:
            try:
                price_per_kwh = float(station['price_per_kWh_INR'])
                # Use the user-selected charger power
                total_amount = price_per_kwh * charger_power * duration
            except Exception as e:
                print(f"Error calculating cost: {e}")
                total_amount = 100.0 * duration
        else:
            total_amount = 100.0 * duration
        
        booking_id = create_booking(
            user_id, station_id, booking_date, 
            booking_time, duration, total_amount
        )
        
        if booking_id:
            f.flash(f"Booking confirmed! ₹{total_amount:.2f} deducted.", "success")
            return f.redirect(f.url_for("main.my_bookings"))
        else:
            f.flash("Insufficient wallet balance!", "danger")
            return f.redirect(f.url_for("main.user_wallet"))
    
    # GET request - show booking form
    from datetime import datetime
    df = as_dataframe()
    station = df[df['station_id'] == station_id].to_dict('records')[0] if len(df) > 0 else None
    wallet_balance = get_wallet_balance(user_id)
    
    return f.render_template("book_station.html", 
                           station=station, 
                           wallet_balance=wallet_balance,
                           now=datetime.now())


@bp.route("/bookings")
def my_bookings():
    """Show user's bookings."""
    if not f.session.get("user_id"):
        f.flash("Please login", "warning")
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    bookings = get_user_bookings(user_id)
    
    return f.render_template("user_bookings_list.html", bookings=bookings)


@bp.route("/booking/cancel/<int:booking_id>", methods=["POST"])
def cancel_booking_route(booking_id: int):
    """Cancel a booking."""
    if not f.session.get("user_id"):
        return f.redirect(f.url_for("main.user_login"))
    
    user_id = f.session.get("user_id")
    
    if cancel_booking(booking_id, user_id):
        f.flash("Booking cancelled! Amount refunded.", "success")
    else:
        f.flash("Failed to cancel booking", "danger")
    
    return f.redirect(f.url_for("main.my_bookings"))


@bp.route("/admin/bookings")
def admin_bookings():
    """View all bookings (admin only)."""
    if not require_admin():
        return f.redirect(f.url_for("main.admin_login"))
    
    bookings = get_all_bookings()
    return f.render_template("admin_bookings.html", bookings=bookings)

