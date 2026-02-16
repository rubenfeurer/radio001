# Tasks: Fix Docker Audio Playback

- [x] Add `mpg123` and `alsa-utils` to Dockerfile apt-get install
- [x] Remove `python-mpv` from `backend/requirements.txt`
- [x] Rewrite `AudioPlayer` to use mpg123 subprocess instead of MPV bindings
- [x] Rewrite `AudioPlayer.set_volume` to use amixer for ALSA volume control
- [x] Rebuild Docker image and verify audio playback works
