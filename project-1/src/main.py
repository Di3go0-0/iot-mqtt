from wifi_connection import connect
from captive_portal import start_portal
from network_params import read_params

# Intentar con credenciales guardadas
ssid, password = read_params()

if ssid and password:
    print("Credenciales encontradas, intentando conexión...")
    if connect(ssid, password):
        print("Conectado al WiFi!")
    else:
        print("Falló la conexión, lanzando portal de configuración...")
        start_portal()
else:
    print("Sin credenciales guardadas, lanzando portal de configuración...")
    start_portal()
