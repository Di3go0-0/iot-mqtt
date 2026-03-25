from machine import Pin

boton = Pin(23, Pin.IN, Pin.PULL_UP)
_previo = 1


def fue_presionado():
    global _previo
    estado = boton.value()
    presionado = estado == 0 and _previo == 1
    _previo = estado
    return presionado
