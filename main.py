from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Zoho-gegevens uit environment variabelen
CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
ORG_ID = os.getenv("ZOHO_ORG_ID")

def get_access_token():
    url = "https://accounts.zoho.eu/oauth/v2/token"
    params = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, params=params)
    return response.json().get("access_token")

@app.route("/order", methods=["GET"])
def get_order():
    order_id = request.args.get("order_id")

    if not order_id:
        return jsonify({"error": "order_id is vereist"}), 400

    token = get_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }

    url = f"https://inventory.zoho.eu/api/v1/salesorders?organization_id={ORG_ID}&search_text={order_id}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "Fout bij ophalen van bestelgegevens", "details": response.text}), 500

    orders = response.json().get("salesorders", [])
    for order in orders:
        if order_id == order.get("salesorder_number"):
            return jsonify({
                "order_id": order["salesorder_id"],
                "order_number": order["salesorder_number"],
                "date": order["date"],
                "status": order["status"],
                "total": order["total"],
                "customer": order.get("customer_name")
            })

    return jsonify({"message": "Geen bestelling gevonden met dit ordernummer."})

if __name__ == "__main__":
    app.run()
