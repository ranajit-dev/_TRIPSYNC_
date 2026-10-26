# TRIPSYNC v1.2 — Login redesign

## Design changes
- The `/login` page shares the editorial green/cream theme, Manrope/DM Sans typography, compass wordmark, and full-height travel photography used by the public landing page.
- Two-column responsive design: scenic image and content on the left; simple, highly readable sign-in form on the right. On phones the layout stacks, and navigation remains visible.
- Gentle entrance/landscape/orbit animations with `prefers-reduced-motion` support.
- New navigation includes **Back to the website** (`/`) and **Return to Dashboard** (`/dashboard`). The dashboard route remains protected: unauthenticated visitors are redirected to sign in.
- If an authenticated user visits `/login`, the page shows **Already in sync** and a **Return to Dashboard** CTA instead of asking them to log in again.
- Firebase SDK initialization, login form IDs, client-side token exchange, anti-CSRF input, and account authorization remain unchanged.
- A standalone `static/css/login.css` style sheet avoids modifying the Admin UI's CSS.

## Merge into your locally configured app

1. Back up the existing project.
2. Replace `app.py` and `templates/login.html` with the files in this ZIP.
3. Add `static/css/login.css`.
4. Keep the v1.1 landing assets: `templates/landing.html`, `static/css/landing.css`, `static/js/landing.js`.
5. **Keep your own `.env`, `serviceAccountKey.json`, and `venv/`**. Neither credentials nor virtual environments are part of the ZIP.
6. Restart with `python app.py` and browse to `http://127.0.0.1:5000/login` (or visit the public homepage at `/` then choose Login).
7. Run `python -m pytest tests/ -v` with dependencies installed. New UI regression tests are in `tests/test_login_theme.py`.

## Security and data

This visual update does not grant public booking access, change Firestore, add signup, or weaken Firebase role checks. All dashboard and booking routes remain protected. Landscape imagery loads remotely from Unsplash when an internet connection is available. Always keep Firebase service-account JSON and Flask secrets out of Git.
