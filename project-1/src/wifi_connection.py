import network
import utime
from machine import Pin

led = Pin(2, Pin.OUT)


def connect(ssid, password, timeout_ms=5000):
    print("Conectando a WiFi:", ssid)

    sta = network.WLAN(network.WLAN.IF_STA)
    sta.active(False)
    utime.sleep(1)
    sta.active(True)

    if sta.isconnected():
        sta.disconnect()
        utime.sleep(1)

    sta.connect(ssid, password)

    start = utime.ticks_ms()

    while not sta.isconnected():
        if utime.ticks_diff(utime.ticks_ms(), start) > timeout_ms:
            break
        led.on()
        utime.sleep_ms(200)
        led.off()
        utime.sleep_ms(800)

    if sta.isconnected():
        print("Conectado! IP:", sta.ifconfig()[0])
        led.on()
        return True
    else:
        print("No se pudo conectar en", timeout_ms // 1000, "segundos")
        sta.disconnect()
        led.off()
        return False
