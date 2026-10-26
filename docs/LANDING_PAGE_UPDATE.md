# TripSync v1.1 — Public landing-page update

## What changed

- `/` is **always** a public marketing homepage, regardless of authentication state.
- Visitors are no longer sent directly to `/login` when visiting the website root.
- The homepage now includes a pill-shaped top navigation with **Log in**, **Discover**, **Experience** and **How it works**.
- Signed-in users see **Dashboard / Open workspace** instead of a redundant sign-in call to action.
- Added editorial, travel-photography layout inspired by the supplied reference video: scenic hero, alternating photo/text panels, editorial typography, forest feature section, full-bleed final CTA.
- Added staged hero animation, section scroll-reveal, subtle image zoom, animated ticker, header scroll state, and responsive mobile navigation.
- `prefers-reduced-motion` disables movement for users who request it.
- The sign-in page now includes a link **Back to the website**.
- Protected booking, dashboard, reporting, and data routes are unaffected by the public homepage.
- Added six regression tests in `tests/test_landing.py`.

## Run locally

1. Extract the ZIP into a clean project folder (or merge the changes into your existing project while keeping your local `.env` and `serviceAccountKey.json`).
2. Activate your virtual environment and run `pip install -r requirements.txt` if dependencies are not already installed.
3. Start the app with `python app.py`.
4. Browse to **http://127.0.0.1:5000/** to view the new landing page.
5. Click **Log in** on the top navigation to reach `/login`; sign in using your existing Firebase account.
6. Once authenticated, the homepage's button becomes **Open workspace**, and `/dashboard` remains restricted to authenticated Admin/Staff.
7. To test: `python -m pytest tests/ -v`.

## Visual assets

The landscape imagery uses public HTTPS image URLs hosted on Unsplash and requires an internet connection to appear. The new CSS includes background colors/gradients to prevent blank sections if remote images fail; for a fully offline deployment, replace the URLs with your own licensed local photos. Photo image use subject to the [Unsplash license](https://unsplash.com/license). The server Content-Security-Policy already permits HTTPS images.

The new homepage does **not** add public signup or public booking access; accounts remain provisioned through the trusted Admin workflow.

## Security

This package intentionally excludes `.env` and Firebase service account credentials. Keep them in your local project directory and do not commit them to GitHub.
