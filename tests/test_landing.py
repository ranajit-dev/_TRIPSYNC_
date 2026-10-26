"""Public landing-page and authentication-boundary regressions."""
from pathlib import Path


def test_homepage_public_and_editorial(client):
    response = client.get('/')
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'Every journey' in text
    assert 'Less organizing.' in text
    assert 'href="/login"' in text
    assert 'landing.css' in text and 'landing.js' in text
    assert 'id="site-nav"' in text
    assert 'id="main-content"' in text


def test_signed_in_homepage_offers_dashboard(admin_client):
    response = admin_client.get('/')
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'href="/dashboard"' in text
    assert 'Access your workspace' not in text


def test_login_has_a_homepage_link(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Back to the website' in response.data
    assert b'href="/"' in response.data


def test_booking_dashboard_still_require_login(client):
    for path in ['/dashboard', '/bookings', '/bookings/new', '/upcoming', '/reports']:
        response = client.get(path)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


def test_landing_assets_are_local(client):
    for path in ['/static/css/landing.css', '/static/js/landing.js']:
        response = client.get(path)
        assert response.status_code == 200
        assert len(response.data) > 500


def test_landing_has_no_private_admin_content(client):
    page = client.get('/').get_data(as_text=True)
    assert 'admin@tripsync.local' not in page
    assert 'AdminPass123!' not in page
    assert 'FIREBASE_CONFIG' not in page
