# Phase F — GitHub + Render Production Release (v1.3.0)

## Deployment status
This package is **deployment-ready source**, not a claim that a public URL is already live. The maintainer must push the files, configure Render credentials, and complete the production sign-in check.

## 0. Keep credentials private
- NEVER commit `.env`, `serviceAccountKey.json`, a Firebase service account private key, or your Flask `SECRET_KEY`.
- This release contains `.env.example` only; create secrets in Render's private dashboard.
- Rotate any prior Flask signing secret or Admin password exposed in a screenshot. Generate a fresh production `SECRET_KEY` (Render `generateValue: true`).
- Ensure your service account JSON belongs to the same Firebase project as the public Web SDK configuration.

## 1. Push the latest files into the existing GitHub repository
Repository: https://github.com/Animesh-666/TRIPSYNC

Recommended low-conflict method: make a NEW clean clone and copy the contents of this release's `TRIPSYNC` folder into that clone. This retains Git history and preserves any remotely tracked files not included in the release.

PowerShell (run from Desktop, adjusting paths to your extracted folder):

```powershell
cd "$HOME\Desktop"
git clone https://github.com/Animesh-666/TRIPSYNC.git TRIPSYNC-publish
# Extract the ZIP, then copy the CONTENTS of its TRIPSYNC folder into TRIPSYNC-publish.
# On a fresh clone, the overlay can be made in Explorer or with the next command:
robocopy '.\TRIPSYNC_v1.3.0_Phase_F_Deployment_Ready\TRIPSYNC' '.\TRIPSYNC-publish' /E /XD .git venv __pycache__ /XF .env serviceAccountKey.json
# Robocopy exit codes 0-7 are normal/nonfatal; do not use /MIR.
cd '.\TRIPSYNC-publish'
git status --short
git check-ignore .env serviceAccountKey.json
# The next line must be EMPTY:
git ls-files .env serviceAccountKey.json
git add -A
git diff --cached --stat
git commit -m "Release TripSync v1.3.0: animated site and production deployment"
git push origin main
```

**Important:** The `Copy-Item` path depends on where you actually extracted the ZIP. If you used a different folder name, adjust the path. Verify staged files with `git diff --cached --stat` before committing. Do not copy your working `venv`, `.env`, or service key into the clone.

If you use existing `TRIPSYNC` working folder, fetch/pull first and watch for local modifications, or use the clean-clone method above.

## 2. Deploy to Render
1. Open https://dashboard.render.com/ and log into your own Render account.
2. Choose **New → Web Service**; connect **GitHub** and select `Animesh-666/TRIPSYNC` on `main`. (Alternative: **New → Blueprint** and import this repo's `render.yaml`.)
3. Choose Python runtime, Python 3.11.9, and a Render plan you intend to use.
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 app:app`
6. Set **Health Check Path** to `/readyz`. The response is HTTP 200 if an SDK Firestore client initialized; it does not prove external reads/writes, so additionally verify a real booking.
7. Set auto deploy from `main` if desired.

### Render Environment variables

| Key | Value |
| --- | --- |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `0` |
| `PYTHON_VERSION` | `3.11.9` |
| `SECRET_KEY` | Random freshly generated value (Render Generate) |
| `GOOGLE_APPLICATION_CREDENTIALS` | `/etc/secrets/serviceAccountKey.json` |
| `FIREBASE_PROJECT_ID` | Firebase Project Settings → `projectId` |
| `FIREBASE_API_KEY` | Firebase web config → `apiKey` |
| `FIREBASE_AUTH_DOMAIN` | Firebase web config → `authDomain` |
| `FIREBASE_STORAGE_BUCKET` | Firebase web config → `storageBucket` |
| `FIREBASE_MESSAGING_SENDER_ID` | Firebase web config → `messagingSenderId` |
| `FIREBASE_APP_ID` | Firebase web config → `appId` |

In Render **Environment → Secret Files → Add Secret File**, name the file `serviceAccountKey.json` and paste its contents from your local, private Firebase Admin SDK file **inside the Render dashboard only**. Never paste that file into chat or GitHub. The file will be mounted at `/etc/secrets/serviceAccountKey.json`.

Blueprint initial creation prompts for `sync: false` Firebase web-config values; manually add the private Secret File before expecting the readiness probe to pass.

## 3. Authorize the public Render origin
Firebase Console → Authentication → Settings → Authorized domains → add just the hostname Render assigns (for example, `travel-booking-organizer.onrender.com`; no `https://` and no `/`). Use the real assigned hostname, not a guess. Confirm Email/Password sign-in is enabled. Firebase Auth JS config and Admin service account must be from the same project.

## 4. Verify deployment before release
- Open the actual `https://...onrender.com/` URL: landing page should load.
- `/login` should load and successfully authenticate an authorized Firebase user.
- `/dashboard` without authentication should redirect to login.
- Log in as an existing Admin, confirm Dashboard loads.
- Check `/healthz` and `/readyz` and inspect Render logs if errors occur.
- Create and edit a **fictional** booking, refresh page and ensure Firestore persisted it; test reports, CSV and print.
- Check Mobile navigation and Return-to-Dashboard controls.
- Test signing out and verify that protected routes deny anonymous access.
- Do not upload sensitive customer details as part of testing.

## 5. Optional GitHub release after live verification
Only after successful production checks:

```powershell
git tag -a v1.3.0 -m "TripSync v1.3.0 production release"
git push origin v1.3.0
```

Then add a release from https://github.com/Animesh-666/TRIPSYNC/releases/new and set the GitHub About section's **Website** to the confirmed Render URL. These actions are **not** performed by this ZIP.

## Caveats
- Firebase and Flask runtime tests were **not** run in the artifact preparation environment. The previously supplied user output showed 54 passed + 1 failing cloud-aware test; the latter has been patched to isolate Firestore before asserting failure. The new CI workflow will check the complete test suite on GitHub.
- Render web service creation, adding service-account secrets, and final URL publication require access to your Render account.
