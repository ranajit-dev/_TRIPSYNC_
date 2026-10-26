"""TripSync editorial login UI and protected return-navigation regressions."""


def test_guest_login_uses_editorial_design_and_retains_firebase_form(client):
    response = client.get('/login')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'css/login.css' in page
    assert 'css/landing.css' in page
    assert 'Welcome' in page and 'back.' in page
    assert 'id="login-form"' in page
    assert 'id="email"' in page
    assert 'id="password"' in page
    assert 'id="login-btn"' in page
    assert 'id="login-spinner"' in page
    assert 'id="login-error"' in page
    assert 'id="toggle-password"' in page
    assert 'js/firebase-auth.js' in page
    assert 'name="_csrf_token"' in page


def test_login_nav_links_home_and_protected_dashboard(client):
    page = client.get('/login').get_data(as_text=True)
    assert 'Back to the website' in page
    assert 'Return to Dashboard' in page
    assert 'href="/"' in page
    assert 'href="/dashboard"' in page
    # A guest cannot use the shortcut to bypass the auth check.
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_signed_in_login_offers_dashboard_without_reauthentication(admin_client):
    response = admin_client.get('/login')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'Already' in page and 'in sync.' in page
    assert 'Return to Dashboard' in page
    assert 'href="/dashboard"' in page
    assert 'id="login-form"' not in page
    assert 'firebase-auth.js' not in page


def test_login_theme_asset_loads(client):
    response = client.get('/static/css/login.css')
    assert response.status_code == 200
    assert len(response.data) > 1000
    assert b'prefers-reduced-motion' in response.data


def test_login_does_not_restore_demo_credentials(client):
    page = client.get('/login').get_data(as_text=True)
    assert 'AdminPass123' not in page
    assert 'demo_mode' not in page
