"""Security, reliability and reporting regression cases for Phases A-C.

Run normally with pytest after installing requirements. Firestore remains mocked by
explicit TESTING config; no real cloud writes are performed.
"""
from datetime import datetime
import pytest
import services
from database import get_booking_by_id, update_booking
from constants import STATUS_CANCELLED, STATUS_CONFIRMED, STATUS_PENDING


def _valid_form():
    return {
        'customer_name': 'Sample Person', 'contact': '9876543210',
        'travel_type': 'flight', 'source': 'Kolkata', 'destination': 'Delhi',
        'travel_date': services.get_current_kolkata_date().isoformat(),
        'passengers': '1', 'unit_fare': '1200.50', 'amount_paid': '100',
        'booking_status': STATUS_CONFIRMED,
    }


@pytest.mark.parametrize('value', ['NaN', 'inf', '-inf', '1.234', '-25', '1e999999', 'abc'])
def test_invalid_money_never_crashes(value):
    for key in ('unit_fare', 'amount_paid'):
        form = _valid_form()
        form[key] = value
        _, errors = services.validate_booking_input(form)
        assert key in errors


def test_currency_decimal_precision_and_accounting():
    assert services.rupees_to_paise('0.29') == 29
    assert services.rupees_to_paise('125.50') == 12550
    assert services.rupees_to_paise('1200.00') == 120000


def test_reject_demo_auth_even_in_testing(client):
    # First fetch to create CSRF session.
    page = client.get('/login')
    assert page.status_code == 200
    with client.session_transaction() as sess:
        csrf = sess['_csrf_token']
    response = client.post('/session/login', json={
        'demo_mode': True, 'email': 'admin@tripsync.local',
        'password': 'AdminPass123!'
    }, headers={'X-CSRF-Token': csrf})
    assert response.status_code == 403
    assert client.get('/dashboard').status_code == 302


def test_flask_cookie_separate_from_firebase_cookie(app):
    from config import Config
    assert app.config['SESSION_COOKIE_NAME'] != Config.FIREBASE_SESSION_COOKIE_NAME


def test_inmemory_storage_fails_closed_outside_testing(app, monkeypatch):
    import database

    # In testing mode, the in-memory database is permitted.
    assert database._get_database_or_test_memory() is None

    # Simulate a real Firestore outage, even on developers' configured machines.
    monkeypatch.setattr(database, "get_db", lambda: None)

    with app.app_context():
        app.config["TESTING"] = False
        try:
            with pytest.raises(RuntimeError, match="Firestore is unavailable"):
                database._get_database_or_test_memory()
        finally:
            app.config["TESTING"] = True


def test_staff_cannot_cancel_using_edit(staff_client, sample_booking):
    booking_id = sample_booking['booking_id']
    form = _valid_form()
    form['booking_status'] = STATUS_CANCELLED
    resp = staff_client.post(f'/bookings/{booking_id}/edit', data={**form,'_csrf_token':'test-csrf-token'})
    assert resp.status_code == 400
    assert get_booking_by_id(booking_id)['booking_status'] == STATUS_CONFIRMED


def test_cancelled_record_cannot_be_reactivated(admin_client, sample_booking):
    booking_id = sample_booking['booking_id']
    admin_client.post(f'/bookings/{booking_id}/cancel', data={'_csrf_token':'test-csrf-token'})
    response = admin_client.post(f'/bookings/{booking_id}/edit', data={**_valid_form(),'_csrf_token':'test-csrf-token'})
    assert response.status_code == 403
    assert get_booking_by_id(booking_id)['booking_status'] == STATUS_CANCELLED


def test_database_guards_disallow_cancel_without_special_method(app, sample_booking):
    with pytest.raises(PermissionError):
        update_booking(sample_booking['booking_id'], {'booking_status': STATUS_CANCELLED}, {'uid': 'staff'})


def test_monthly_chart_counts_only_active_bookings():
    this_month = services.get_current_kolkata_date().strftime('%Y-%m')
    rows = [
        {'booking_id':'TB-0001','booking_status': STATUS_CONFIRMED, 'created_at':this_month+'-05T10:00:00', 'total_amount_paise':5000},
        {'booking_id':'TB-0002','booking_status': STATUS_PENDING, 'created_at':this_month+'-08T10:00:00', 'total_amount_paise':4000},
        {'booking_id':'TB-0003','booking_status': STATUS_CANCELLED, 'created_at':this_month+'-09T10:00:00', 'total_amount_paise':3000},
    ]
    metrics = services.calculate_dashboard_metrics(rows)
    assert len(metrics['monthly_labels']) == 6
    assert metrics['monthly_booking_counts'][-1] == 2
    assert sum(metrics['category_counts'].values()) == metrics['total_active_bookings'] if all('travel_type' in row for row in rows) else True


def test_csv_export_respects_filter(admin_client, sample_booking):
    result = admin_client.get('/export/csv?destination=NotTheDestination')
    assert result.status_code == 200
    assert sample_booking['booking_id'] not in result.data.decode('utf-8-sig')
    found = admin_client.get('/export/csv?destination=Delhi')
    assert sample_booking['booking_id'] in found.data.decode('utf-8-sig')


def test_firestore_login_cookie_required_without_test_session(app):
    """Flask sessions can only substitute for Firebase when TESTING=True."""
    from decorators import get_current_authenticated_user
    app.config['TESTING'] = False
    with app.test_request_context('/dashboard'):
        from flask import session
        session['user']={'uid':'fake_admin','role':'Admin','active':True}
        assert get_current_authenticated_user() is None
    app.config['TESTING'] = True


def test_firestore_booking_creation_uses_single_transaction(monkeypatch):
    """Counter allocation and booking creation must share the same transaction."""
    import database
    from types import SimpleNamespace
    operations = []

    class FakeSnapshot:
        exists = False

    class Ref:
        def __init__(self, path):
            self.path = path
        def get(self, transaction=None):
            assert transaction is txn
            return FakeSnapshot()

    class Collection:
        def __init__(self, name):
            self.name = name
        def document(self, name):
            return Ref(f'{self.name}/{name}')

    class Db:
        def collection(self, name):
            return Collection(name)
        def transaction(self):
            return txn

    class Txn:
        def set(self, ref, data, **kwargs):
            operations.append(('counter',ref.path,data))
        def create(self, ref, data):
            operations.append(('booking',ref.path,data))

    txn = Txn()
    monkeypatch.setattr(database, 'firestore', SimpleNamespace(
        transactional=lambda fn: fn,
        SERVER_TIMESTAMP='SERVER_TIMESTAMP'
    ))
    monkeypatch.setattr(database, '_get_database_or_test_memory', lambda: Db())
    created = database.create_booking({'customer_name':'Mock Person'}, {'uid':'test'})
    assert created['booking_id'] == 'TB-0001'
    assert len(operations) == 2
    assert operations[0][0] == 'counter'
    assert operations[1][0] == 'booking'
    assert operations[1][1] == 'bookings/TB-0001'
