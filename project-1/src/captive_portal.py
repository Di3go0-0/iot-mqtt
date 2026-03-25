import network
import socket
from wifi_connection import connect
from network_params import write_params

PORTAL_HTML = """\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configurar WiFi</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #1a1a2e; color: #eee; }
        input { padding: 10px; margin: 5px; width: 200px; border-radius: 5px; border: 1px solid #444; }
        button { padding: 10px 30px; margin-top: 10px; background: #0f3460; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #16213e; }
        h2 { color: #e94560; }
    </style>
</head>
<body>
    <h2>Configurar WiFi</h2>
    <form action="/" method="get">
        <input name="ssid" placeholder="Nombre de la red"><br>
        <input name="password" type="password" placeholder="Contraseña"><br>
        <button type="submit">Conectar</button>
    </form>
</body>
</html>
"""

SUCCESS_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Conectado</title>
<style>body{font-family:sans-serif;text-align:center;margin-top:50px;background:#1a1a2e;color:#eee;}h2{color:#0f3460;}</style>
</head>
<body><h2>Conectado exitosamente!</h2><p>El ESP32 se ha conectado a la red WiFi.</p></body>
</html>
"""


def start_portal(ap_ssid="esp32ghoul", ap_password="1223334444"):
    ap = network.WLAN(network.WLAN.IF_AP)
    ap.active(True)
    ap.config(essid=ap_ssid, password=ap_password, authmode=3)

    print("AP activo:", ap_ssid)
    print("IP del portal:", ap.ifconfig()[0])

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 80))
    server.listen(1)

    print("Portal cautivo escuchando en puerto 80...")

    try:
        while True:
            conn, addr = server.accept()
            request = conn.recv(1024).decode()
            request_line = request.split("\n")[0] if request else ""

            # Revisar si viene con parámetros ssid y password
            if "ssid=" in request_line:
                path = request_line.split(" ")[1]
                query = path.split("?")[1]
                params = {}
                for pair in query.split("&"):
                    key, value = pair.split("=", 1)
                    params[key] = value

                ssid = params.get("ssid", "")
                password = params.get("password", "")

                if ssid:
                    print("Intentando conectar a:", ssid)
                    if connect(ssid, password):
                        write_params(ssid, password)
                        _send_response(conn, SUCCESS_HTML)
                        conn.close()
                        ap.active(False)
                        break
                    else:
                        _send_response(conn, PORTAL_HTML)
                        conn.close()
                        continue

            _send_response(conn, PORTAL_HTML)
            conn.close()

    except KeyboardInterrupt:
        print("Cerrando portal...")
    finally:
        server.close()


def _send_response(conn, html):
    conn.send(b"HTTP/1.1 200 OK\r\n")
    conn.send(b"Content-Type: text/html\r\n")
    conn.send(b"Connection: close\r\n\r\n")
    conn.sendall(html.encode())
