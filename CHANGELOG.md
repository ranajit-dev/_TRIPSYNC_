# TRIPSYNC Release Candidate v1.3.0

The current production-ready source includes the v1.2.1 animated homepage and login, protected Admin/Staff dashboard navigation, Firebase Auth + Firestore storage, enhanced analytics and filtered CSV reports.

**Release improvements**
- Gunicorn binds Render's `$PORT` on `0.0.0.0`.
- Render `/readyz` health check and environment configuration with explicit production mode.
- GitHub Actions runs syntax compilation and the automated regression suite on pushes to `main`.
- Fixed the mocked Firestore-outage regression test so it does not depend on whether a developer's real Firebase connection is available.
- Expanded `.gitignore` to cover more local credential file patterns.
- Added a complete production deployment checklist.

**Live deployment and a production release tag have NOT been performed by this package.**
