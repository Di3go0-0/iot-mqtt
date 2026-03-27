from machine import Pin
import utime

boton = Pin(23, Pin.IN, Pin.PULL_UP)
_previo = 1
_toggle = 1
_ultimo_ms = 0
DEBOUNCE_MS = 500


def fue_presionado():
    global _previo, _toggle, _ultimo_ms
    estado = boton.value()
    presionado = estado == 0 and _previo == 1
    _previo = estado
    if presionado and utime.ticks_diff(utime.ticks_ms(), _ultimo_ms) > DEBOUNCE_MS:
        _ultimo_ms = utime.ticks_ms()
        _toggle = 1 - _toggle
        return True, _toggle
    return False, None
