# Tasks: GPIO lgpio Migration

## gpio_controller.py

- [x] Rewrite `_initialize_hardware()` to use lgpio (gpiochip_open, gpio_claim_input, callback)
- [x] Update `_handle_button_event` signature from `(gpio, level, tick)` to `(chip, gpio, level, timestamp)`
- [x] Update `_handle_rotary_event` signature and replace `self._pi.read()` with `lgpio.gpio_read()`
- [x] Update `cleanup()` to use `lgpio.gpiochip_close()` instead of `pi.stop()`
- [x] Update `get_hardware_info()` to remove pigpio fields

## requirements.txt

- [x] Confirm `lgpio` is in requirements (already done via sed)

## docker-compose.prod.yml

- [x] Add `/dev/gpiochip0` device mount to radio-backend service
