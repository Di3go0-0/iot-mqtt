import network
import socket
import utime
from wifi_connection import connect

PORTAL_HTML = """\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiFi Setup</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #1a1a2e; color: #eee; }
        input { padding: 10px; margin: 5px; width: 200px; border-radius: 5px; border: 1px solid #444; }
        button { padding: 10px 30px; margin-top: 10px; background: #0f3460; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #16213e; }
        h2 { color: #e94560; }
        #status { margin-top: 15px; color: #f0a500; display: none; }
    </style>
</head>
<body>
    <h2>WiFi Setup</h2>
    <form id="wform" action="/" method="get">
        <input name="ssid" placeholder="Network name (SSID)"><br>
        <input name="password" type="password" placeholder="Password"><br>
        <button type="submit">Connect</button>
    </form>
    <p id="status">Trying to connect...</p>
    <script>
        document.getElementById('wform').onsubmit = function() {
            document.getElementById('status').style.display = 'block';
        };
    </script>
</body>
</html>
"""

SUCCESS_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Connected</title>
<style>body{font-family:sans-serif;text-align:center;margin-top:50px;background:#1a1a2e;color:#eee;}h2{color:#0f3460;}</style>
</head>
<body><h2>Connected successfully!</h2><p>The ESP32 is now connected to the WiFi network.</p></body>
</html>
"""

ERROR_HTML = """\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connection Error</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #1a1a2e; color: #eee; }
        input { padding: 10px; margin: 5px; width: 200px; border-radius: 5px; border: 1px solid #444; }
        button { padding: 10px 30px; margin-top: 10px; background: #0f3460; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #16213e; }
        h2 { color: #e94560; }
        .error { color: #e94560; margin-bottom: 15px; }
        #status { margin-top: 15px; color: #f0a500; display: none; }
    </style>
</head>
<body>
    <h2>Connection Error</h2>
    <p class="error">Invalid credentials or network not found. Please try again.</p>
    <form id="wform" action="/" method="get">
        <input name="ssid" placeholder="Network name (SSID)"><br>
        <input name="password" type="password" placeholder="Password"><br>
        <button type="submit">Connect</button>
    </form>
    <p id="status">Trying to connect...</p>
    <script>
        document.getElementById('wform').onsubmit = function() {
            document.getElementById('status').style.display = 'block';
        };
    </script>
</body>
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
                        _send_response(conn, SUCCESS_HTML)
                        conn.close()
                        utime.sleep(3)
                        ap.active(False)
                        break
                    else:
                        _send_response(conn, ERROR_HTML)
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
