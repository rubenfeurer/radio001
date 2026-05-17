## 1. GPIOController — Triple Press Callback

- [x] 1.1 Add `triple_press_callback: Optional[Callable]` parameter to `GPIOController.__init__` and store it as `self.triple_press_callback`
- [x] 1.2 Update `_handle_triple_press` to invoke `self.triple_press_callback(gpio_pin)` (await if coroutine) instead of only logging; keep the warning log
- [x] 1.3 Add `simulate_triple_press` mock method that fires three sequential presses on `ROTARY_SW` within `TRIPLE_PRESS_INTERVAL`

## 2. RadioManager — Triple Press Event Handler

- [x] 2.1 Add `_handle_triple_press_event(self, gpio_pin: int)` coroutine to `RadioManager`; in mock mode log warning and return, in production call `subprocess.run(["reboot"])`
- [x] 2.2 Pass `triple_press_callback=self._handle_triple_press_event` when constructing `GPIOController` in `_initialize_hardware`

## 3. System API — Reboot Endpoint

- [x] 3.1 Add `POST /api/system/reboot` endpoint to `backend/api/routes/system.py`; in development mode (`NODE_ENV=development`) return success without rebooting; in production schedule `subprocess.run(["reboot"])` after a 1 s delay so the response is sent first
