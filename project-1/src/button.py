from machine import Pin

boton = Pin(23, Pin.IN, Pin.PULL_UP)
_previo = 1
_toggle = 1


def fue_presionado():
    global _previo, _toggle
    estado = boton.value()
    presionado = estado == 0 and _previo == 1
    _previo = estado
    if presionado:
        _toggle = 1 - _toggle
        return True, _toggle
    return False, None
