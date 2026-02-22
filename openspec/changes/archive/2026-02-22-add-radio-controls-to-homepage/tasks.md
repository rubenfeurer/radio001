# Tasks: Add Radio Controls to Homepage

- [x] Fix WebSocket handler to listen for `stations_update` (backend sends this, not `stations_list`)
- [x] Update radio store to use slot-based station model matching backend (Dict<int, RadioStation|null>) and use REST API for actions
- [x] Update frontend RadioStation type to match backend model (add slot, location; remove id, favicon)
- [x] Add radio imports, state, and onMount lifecycle to homepage
- [x] Add Radio card UI section with now-playing status, 3 station slot buttons, and volume slider
