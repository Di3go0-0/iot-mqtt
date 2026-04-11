import json

CREDS_FILE = "wifi_creds.json"


def save_credentials(ssid, password):
    creds = load_all_credentials()
    # Actualizar si ya existe, o agregar
    for c in creds:
        if c["ssid"] == ssid:
            c["password"] = password
            break
    else:
        creds.append({"ssid": ssid, "password": password})

    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f)
    print("Credenciales guardadas para:", ssid)


def load_all_credentials():
    try:
        with open(CREDS_FILE, "r") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []
