"""
Main Flask Web Application for Travel Booking Data Organizer.
Exposes all routes, template filters, security handlers, and WSGI entrypoint.
"""

from datetime import datetime, date
import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    Response,
    g,
    abort,
)

from config import Config, config_by_name
from constants import (
    ROLE_ADMIN,
    ROLE_STAFF,
    VALID_CATEGORIES,
    CATEGORY_LABELS,
    CATEGORY_ICONS,
    VALID_BOOKING_STATUSES,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    VALID_PAYMENT_STATUSES,
    STANDARD_DESTINATIONS,
    DEFAULT_PER_PAGE,
)
from firebase_config import initialize_firebase, is_firebase_ready
from database import (
    create_booking,
    get_booking_by_id,
    get_all_bookings,
    update_booking,
    cancel_booking,
    delete_booking,
    get_user_by_uid,
    upsert_user,
)
from auth import (
    verify_id_token_and_get_user,
    create_session_cookie,
    verify_session_cookie,
)
from decorators import (
    login_required,
    admin_required,
    generate_csrf_token,
    validate_csrf,
    get_current_authenticated_user,
)
import services


def create_app(config_name: str = None) -> Flask:
    """Application factory for Flask app."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app_config = config_by_name.get(config_name, Config)
    app.config.from_object(app_config)

    # Never boot production with a missing Flask session signing secret.
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be provided in production")

    # Firebase absence causes protected operations to fail closed, not use volatile data.
    initialize_firebase()

    # ------------------------------------------------------------------------
    # Request Lifecycle & Security Interceptors
    # ------------------------------------------------------------------------

    @app.before_request
    def before_request_hook():
        """Handles CSRF validation and attaches current user if present."""
        # CSRF Protection for state-changing requests (except health check)
        if request.endpoint != "healthz":
            csrf_error = validate_csrf()
            if csrf_error:
                return csrf_error

        # Attach authenticated user only when session verification succeeds.
        g.current_user = get_current_authenticated_user()

    @app.after_request
    def add_security_headers(response):
        """Adds defensive HTTP security headers to all responses."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Content Security Policy (allows Bootstrap, Bootstrap Icons, Chart.js, and Firebase Web SDK)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://www.gstatic.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "connect-src 'self' https://*.googleapis.com https://*.firebaseio.com https://identitytoolkit.googleapis.com; "
            "img-src 'self' data: https:; "
            "frame-src 'self' https://*.firebaseapp.com;"
        )
        response.headers["Content-Security-Policy"] = csp
        return response

    # ------------------------------------------------------------------------
    # Jinja Context Processors and Custom Filters
    # ------------------------------------------------------------------------

    @app.context_processor
    def inject_global_template_context():
        """Injects global variables into all Jinja templates."""
        return {
            "current_user": getattr(g, "current_user", None),
            "csrf_token": generate_csrf_token(),
            "app_name": "TripSync",
            "app_tagline": "Travel Booking Data Organizer",
            "app_version": "1.3.0",
            "current_year": datetime.now().year,
            "categories": VALID_CATEGORIES,
            "category_labels": CATEGORY_LABELS,
            "category_icons": CATEGORY_ICONS,
            "booking_statuses": VALID_BOOKING_STATUSES,
            "payment_statuses": VALID_PAYMENT_STATUSES,
            "standard_destinations": STANDARD_DESTINATIONS,
            "firebase_client_config": Config.get_firebase_client_config(),
            "is_firebase_configured": Config.is_firebase_configured(),
        }

    @app.template_filter("currency_inr")
    def filter_currency_inr(paise):
        """Converts integer paise into formatted INR string."""
        return services.format_currency_inr(paise)

    @app.template_filter("paise_to_rupees")
    def filter_paise_to_rupees(paise):
        """Converts integer paise into rupee float."""
        return services.paise_to_rupees(paise or 0)

    @app.template_filter("date_format")
    def filter_date_format(iso_date_str):
        """Formats ISO date string (YYYY-MM-DD) into readable Indian date."""
        if not iso_date_str:
            return "N/A"
        try:
            d = datetime.strptime(str(iso_date_str)[:10], "%Y-%m-%d").date()
            return d.strftime("%d %b %Y")
        except Exception:
            return str(iso_date_str)

    # ------------------------------------------------------------------------
    # Authentication & Session Routes
    # ------------------------------------------------------------------------

    @app.route("/")
    def index():
        """Public, editorial landing page; never exposes booking data."""
        return render_template("landing.html")

    @app.route("/login")
    def login():
        """Renders the login page."""
        # Keep this page accessible to signed-in users so they can explicitly
        # choose "Return to Dashboard" rather than see the sign-in form.
        return render_template("login.html")

    @app.route("/session/login", methods=["POST"])
    def session_login():
        """
        Receives the Firebase ID token from client-side Firebase Auth,
        verifies it on the server, verifies the Firestore user role,
        and sets a secure session cookie.
        """
        data = request.get_json(silent=True) or request.form
        id_token = data.get("idToken")

        # No backdoor or built-in demo credentials are accepted, in any environment.
        if data.get("demo_mode"):
            return jsonify({"status": "error", "message": "Demo authentication is not supported."}), 403

        if not id_token:
            return jsonify({"status": "error", "message": "ID token missing"}), 400

        user_info = verify_id_token_and_get_user(id_token)
        if not user_info:
            return jsonify({"status": "error", "message": "Invalid credentials or unauthorized account."}), 401

        # Create session cookie
        session_cookie = create_session_cookie(id_token)
        response = jsonify({"status": "success", "user": user_info, "redirect": url_for("dashboard")})

        if not session_cookie:
            return jsonify({"status": "error", "message": "Authentication service unavailable."}), 503

        if session_cookie:
            session.pop("user", None)
            response.set_cookie(
                app.config["FIREBASE_SESSION_COOKIE_NAME"],
                session_cookie,
                max_age=app.config["FIREBASE_SESSION_EXPIRY_SECONDS"],
                httponly=True,
                secure=app.config["SESSION_COOKIE_SECURE"],
                samesite=app.config["SESSION_COOKIE_SAMESITE"],
            )
        return response

    @app.route("/session/logout", methods=["POST"])
    def session_logout():
        """Clears the session cookie and session state."""
        session.clear()
        response = redirect(url_for("login"))
        response.delete_cookie(app.config["FIREBASE_SESSION_COOKIE_NAME"], path="/")
        flash("You have been signed out successfully.", "info")
        return response

    # ------------------------------------------------------------------------
    # Dashboard & Analytics Routes
    # ------------------------------------------------------------------------

    @app.route("/dashboard")
    @login_required
    def dashboard():
        """Main dashboard view with KPIs, upcoming trips, and charts."""
        all_bookings = get_all_bookings()
        metrics = services.calculate_dashboard_metrics(all_bookings)
        upcoming_trips = services.get_upcoming_trips(all_bookings, days_window=7)[:5]
        recent_bookings = services.filter_and_sort_bookings(
            all_bookings, sort_by="created_at", sort_dir="desc"
        )[:5]

        return render_template(
            "dashboard.html",
            metrics=metrics,
            upcoming_trips=upcoming_trips,
            recent_bookings=recent_bookings,
        )

    # ------------------------------------------------------------------------
    # Booking Management Routes (CRUD)
    # ------------------------------------------------------------------------

    @app.route("/bookings")
    @login_required
    def bookings():
        """List bookings with search, filters, sorting, and pagination."""
        search_query = request.args.get("q", "").strip()
        category = request.args.get("category", "all")
        booking_status = request.args.get("status", "all")
        payment_status = request.args.get("payment", "all")
        destination = request.args.get("destination", "all")
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        sort_by = request.args.get("sort_by", "travel_date")
        sort_dir = request.args.get("sort_dir", "asc")
        page = request.args.get("page", 1, type=int)

        all_bookings = get_all_bookings()
        filtered = services.filter_and_sort_bookings(
            bookings=all_bookings,
            search_query=search_query,
            category=category,
            booking_status=booking_status,
            payment_status=payment_status,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

        paginated_bookings, pagination = services.paginate_items(filtered, page=page, per_page=DEFAULT_PER_PAGE)

        # Retain query parameters for pagination links
        query_params = request.args.to_dict()
        query_params.pop("page", None)

        return render_template(
            "bookings.html",
            bookings=paginated_bookings,
            pagination=pagination,
            query_params=query_params,
            search_query=search_query,
            category=category,
            status=booking_status,
            payment=payment_status,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_dir=sort_dir,
            total_records=len(filtered),
        )

    @app.route("/bookings/new")
    @login_required
    def add_booking():
        """Renders the add booking form."""
        today_str = services.get_current_kolkata_date().isoformat()
        return render_template(
            "add_booking.html",
            today=today_str,
            form_data={},
            errors={},
        )

    @app.route("/bookings", methods=["POST"])
    @login_required
    def create_booking_action():
        """Handles submission of a new booking record."""
        cleaned_data, errors = services.validate_booking_input(request.form, is_edit=False)
        if cleaned_data.get("booking_status") == STATUS_CANCELLED:
            errors["booking_status"] = "Use the Admin cancellation action after creating a booking."

        if errors:
            today_str = services.get_current_kolkata_date().isoformat()
            return render_template(
                "add_booking.html",
                today=today_str,
                form_data=request.form,
                errors=errors,
            ), 400

        try:
            created = create_booking(cleaned_data, g.current_user)
            flash(f"Booking {created.get('booking_id')} successfully created!", "success")
            return redirect(url_for("booking_details", booking_id=created.get("booking_id")))
        except Exception:
            app.logger.exception("Unable to create booking")
            flash("Could not save the booking. Please try again later.", "danger")
            today_str = services.get_current_kolkata_date().isoformat()
            return render_template(
                "add_booking.html",
                today=today_str,
                form_data=request.form,
                errors={"general": "Unable to save booking. Please try again."},
            ), 500

    @app.route("/bookings/<booking_id>")
    @login_required
    def booking_details(booking_id: str):
        """Displays detailed view of a single booking."""
        booking = get_booking_by_id(booking_id)
        if not booking:
            abort(404, description=f"Booking '{booking_id}' not found.")

        enriched = services.enrich_booking(booking)
        return render_template("booking_details.html", booking=enriched)

    @app.route("/bookings/<booking_id>/edit")
    @login_required
    def edit_booking(booking_id: str):
        """Renders the edit form for a booking."""
        booking = get_booking_by_id(booking_id)
        if not booking:
            abort(404, description=f"Booking '{booking_id}' not found.")

        if booking.get("booking_status") == STATUS_CANCELLED:
            abort(403, description="Cancelled bookings cannot be modified.")

        # Convert paise to rupees for form input display
        form_data = dict(booking)
        form_data["unit_fare"] = services.paise_to_rupees(booking.get("unit_fare_paise", 0))
        form_data["amount_paid"] = services.paise_to_rupees(booking.get("amount_paid_paise", 0))

        today_str = services.get_current_kolkata_date().isoformat()
        return render_template(
            "edit_booking.html",
            booking=booking,
            form_data=form_data,
            errors={},
            today=today_str,
        )

    @app.route("/bookings/<booking_id>/edit", methods=["POST"])
    @login_required
    def update_booking_action(booking_id: str):
        """Handles saving updates to an existing booking."""
        booking = get_booking_by_id(booking_id)
        if not booking:
            abort(404, description=f"Booking '{booking_id}' not found.")

        if booking.get("booking_status") == STATUS_CANCELLED:
            abort(403, description="Cancelled bookings cannot be modified.")

        cleaned_data, errors = services.validate_booking_input(request.form, is_edit=True)
        if cleaned_data.get("booking_status") == STATUS_CANCELLED:
            errors["booking_status"] = "Use the administrator cancellation action."

        if errors:
            today_str = services.get_current_kolkata_date().isoformat()
            return render_template(
                "edit_booking.html",
                booking=booking,
                form_data=request.form,
                errors=errors,
                today=today_str,
            ), 400

        try:
            updated = update_booking(booking_id, cleaned_data, g.current_user)
            flash(f"Booking {booking_id} updated successfully.", "success")
            return redirect(url_for("booking_details", booking_id=booking_id))
        except Exception:
            app.logger.exception("Unable to update booking")
            flash("Could not update the booking. Please try again later.", "danger")
            today_str = services.get_current_kolkata_date().isoformat()
            return render_template(
                "edit_booking.html",
                booking=booking,
                form_data=request.form,
                errors={"general": "Unable to save booking. Please try again."},
                today=today_str,
            ), 500

    @app.route("/bookings/<booking_id>/cancel", methods=["POST"])
    @admin_required
    def cancel_booking_action(booking_id: str):
        """Admin only: Cancels a booking without deleting historical record."""
        booking = get_booking_by_id(booking_id)
        if not booking:
            abort(404, description=f"Booking '{booking_id}' not found.")

        if booking.get("booking_status") == STATUS_CANCELLED:
            flash("This booking is already cancelled.", "info")
            return redirect(url_for("booking_details", booking_id=booking_id))
        try:
            cancel_booking(booking_id, g.current_user)
        except Exception:
            app.logger.exception("Unable to cancel booking")
            abort(503, description="Booking cancellation temporarily unavailable")
        flash(f"Booking {booking_id} has been marked as Cancelled.", "warning")
        return redirect(url_for("booking_details", booking_id=booking_id))

    @app.route("/bookings/<booking_id>/delete", methods=["POST"])
    @admin_required
    def delete_booking_action(booking_id: str):
        """Admin only: Permanently deletes a booking record."""
        booking = get_booking_by_id(booking_id)
        if not booking:
            abort(404, description=f"Booking '{booking_id}' not found.")

        try:
            delete_booking(booking_id)
        except Exception:
            app.logger.exception("Unable to delete booking")
            abort(503, description="Booking deletion temporarily unavailable")
        flash(f"Booking {booking_id} permanently deleted from records.", "info")
        return redirect(url_for("bookings"))

    @app.route("/bookings/<booking_id>/print")
    @login_required
    def print_booking(booking_id: str):
        """Renders printable internal confirmation voucher with dedicated print CSS."""
        booking = get_booking_by_id(booking_id)
        if not booking:
            abort(404, description=f"Booking '{booking_id}' not found.")

        enriched = services.enrich_booking(booking)
        return render_template("booking_print.html", booking=enriched)

    # ------------------------------------------------------------------------
    # Upcoming Trips View
    # ------------------------------------------------------------------------

    @app.route("/upcoming")
    @login_required
    def upcoming():
        """Displays upcoming trips scheduled within the next 7 days."""
        all_bookings = get_all_bookings()
        upcoming_list = services.get_upcoming_trips(all_bookings, days_window=7)

        return render_template("upcoming.html", trips=upcoming_list)

    # ------------------------------------------------------------------------
    # Reports & Analytics (Admin Only)
    # ------------------------------------------------------------------------

    @app.route("/reports")
    @admin_required
    def reports():
        """Admin only: Comprehensive analytics and breakdown charts."""
        all_bookings = get_all_bookings()
        metrics = services.calculate_dashboard_metrics(all_bookings)

        return render_template("reports.html", metrics=metrics)

    # ------------------------------------------------------------------------
    # Data Export (Admin Only)
    # ------------------------------------------------------------------------

    @app.route("/export/csv")
    @admin_required
    def export_csv():
        """Admin only: Exports booking dataset as a secure CSV."""
        all_bookings = get_all_bookings()
        query = request.args
        filtered = services.filter_and_sort_bookings(
            all_bookings,
            search_query=query.get("q", ""),
            category=query.get("category", "all"),
            booking_status=query.get("status", "all"),
            payment_status=query.get("payment", "all"),
            destination=query.get("destination", "all"),
            start_date=query.get("start_date", ""),
            end_date=query.get("end_date", ""),
            sort_by=query.get("sort_by", "travel_date"),
            sort_dir=query.get("sort_dir", "asc"),
        )
        csv_data = services.generate_bookings_csv(filtered)

        filename = f"travel_bookings_{services.get_current_kolkata_date().isoformat()}.csv"
        # Prepend UTF-8 BOM so Excel opens Indian names and characters properly
        response_bytes = "\ufeff" + csv_data

        return Response(
            response_bytes,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # ------------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------------

    @app.route("/healthz")
    def healthz():
        """Minimal health check endpoint for monitoring without sensitive leakage."""
        return jsonify({
            "status": "healthy",
            "service": "travel-booking-organizer",
            "version": "1.3.0",
            "firebase_ready": is_firebase_ready(),
        }), 200

    @app.route("/readyz")
    def readyz():
        """Readiness check: storage client must be initialized (network verification separate)."""
        ready = is_firebase_ready()
        return jsonify({"status": "ready" if ready else "unavailable"}), 200 if ready else 503

    # ------------------------------------------------------------------------
    # Error Handlers
    # ------------------------------------------------------------------------

    @app.errorhandler(400)
    def bad_request_error(e):
        return render_template("errors/500.html", error_code=400, error_message=getattr(e, "description", "Bad Request")), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template("errors/404.html", error_message=getattr(e, "description", "Page Not Found")), 404

    @app.errorhandler(RuntimeError)
    def database_error(e):
        app.logger.exception("Runtime service failure: %s", e)
        return render_template("errors/500.html", error_code=503, error_message="Booking database temporarily unavailable."), 503

    @app.errorhandler(503)
    def service_unavailable_error(e):
        return render_template("errors/500.html", error_code=503, error_message="Service temporarily unavailable. Please try again later."), 503

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html", error_code=500, error_message="An internal server error occurred."), 500

    return app


# WSGI application object for Gunicorn / Render
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
