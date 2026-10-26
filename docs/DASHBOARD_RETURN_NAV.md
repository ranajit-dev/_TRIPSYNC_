# Dashboard return navigation — v1.2.1

Added a lightweight back-navigation action to the shared authenticated header (`templates/_navbar.html`).

- On the main dashboard (`/dashboard`): **Back to Website** opens the public landing page (`/`).
- On bookings, new/edit booking, upcoming trips, and reports: **Back to Dashboard** opens (`/dashboard`).
- Links go to named Flask routes (`url_for`) and do not depend on browser history.
- Existing sidebar, login, Firebase session, roles, and booking logic are unchanged.
- Responsive label text and accessible focus styles included in `static/css/components.css`.

## Upgrade an existing local TRIPSYNC install

Copy just `templates/_navbar.html` and `static/css/components.css` from the patch ZIP into your existing `TRIPSYNC` folder, preserving its `.env`, `serviceAccountKey.json`, and `venv`.
Restart `python app.py`, then hard refresh Chrome with `Ctrl + Shift + R`.

Do not copy a credential file into the ZIP or commit one to GitHub.
