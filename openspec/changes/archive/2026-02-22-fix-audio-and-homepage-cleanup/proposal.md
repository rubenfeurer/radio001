## Why

Two issues found after implementing the radio homepage:

1. **Audio doesn't play despite the UI showing "playing":** `stations.json` contains 28k radio.garden URLs. Radio.garden returns HTTP 403 (Cloudflare challenge) to mpg123's user agent — blocking all streams. mpg123 itself works correctly with direct stream URLs (confirmed with SRF3). The station library needs to be replaced or supplemented with streams that mpg123 can access directly.

2. **"Now Playing" row is redundant:** The active slot card already shows the station name with a pulsing indicator. The separate "Now Playing" row above the slot cards duplicates this information.

## What Changes

### Fix: Station library URLs
- Replace `config/stations.json` with stations that use direct MP3/AAC stream URLs (not radio.garden redirect URLs)
- Or: add a curated set of working direct-stream stations as the default library, keeping radio.garden entries for reference but flagging them
- Simplest fix: replace the library with a working set of direct-stream stations from public sources

### Fix: mpg123 user-agent for radio.garden (alternative)
- Pass `--user-agent` to mpg123 to spoof a browser UA, allowing radio.garden streams to work
- This avoids replacing the entire station library

### Cleanup: Remove "Now Playing" row from homepage
- Delete the now-playing status row (station name + location) above the slot cards in `+page.svelte`
- The active slot card already shows name + pulsing indicator — no information is lost

## Capabilities

### Modified Capabilities
- `homepage-radio-controls`: Remove redundant now-playing row
- `audio-playback`: mpg123 streams radio.garden URLs successfully via spoofed user-agent

### No New Capabilities

## Impact

- `backend/hardware/audio_player.py`: Add `--user-agent "Mozilla/5.0"` arg to mpg123 subprocess call
- `frontend/src/routes/+page.svelte`: Remove the "Now Playing" `<div>` block (~10 lines)
- No changes to station library files, backend routes, or stores
