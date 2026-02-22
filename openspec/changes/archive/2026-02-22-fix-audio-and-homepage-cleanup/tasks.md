# Tasks: Fix Audio Output and Homepage Cleanup

## Backend

- [x] Add `_resolve_url()` helper to `backend/hardware/audio_player.py`: uses curl with a browser UA to follow redirects and return the final stream URL before passing to mpg123
  - Root cause: radio.garden URLs 302-redirect to direct MP3 streams, but only for browser UAs. mpg123 gets 403 on the redirect. mpg123 1.32 has no `--user-agent` flag.
  - Fix: resolve redirect via curl first, hand mpg123 the direct URL

## Frontend

- [x] Remove redundant "Now Playing" row from Radio card in `frontend/src/routes/+page.svelte`
- [x] Remove unused `currentStation` import from homepage script

## Deployment

- [x] Rebuild Docker backend image and restart container

## Verification

- [x] Selecting a radio.garden station plays audio through the Pi headphone jack
- [x] Homepage radio card shows slot cards only, no separate now-playing row
