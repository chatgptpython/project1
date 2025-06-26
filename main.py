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

@app.route("/order", methods=["GET", "POST"])
def get_order():
    # Ondersteun zowel GET als POST
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email")
        order_id = data.get("order_id")
    else:  # GET
        email = request.args.get("email")
        order_id = request.args.get("order_id")

    if not email or not order_id:
        return jsonify({"error": "email and order_id required"}), 400

    token = get_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }

    url = f"https://www.zohoapis.eu/inventory/v1/salesorders?organization_id={ORG_ID}&search_text={order_id}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({
            "error": "Failed to retrieve order data",
            "details": response.text
        }), 500

    orders = response.json().get("salesorders", [])
    for order in orders:
        if email.lower() in order.get("customer_name", "").lower():
            return jsonify({
                "order_id": order["salesorder_id"],
                "date": order["date"],
                "status": order["status"],
                "total": order["total"]
            })

    return jsonify({"message": "Geen bestelling gevonden met deze gegevens."})

if __name__ == "__main__":
    app.run()
