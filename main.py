from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Haal Zoho-credentials uit environment variabelen
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
    print(">> Access token opvragen...")
    response = requests.post(url, params=params)
    print(">> Access token response:", response.status_code, response.text)
    return response.json().get("access_token")

def get_customer_email(customer_id, token):
    url = f"https://www.zohoapis.eu/inventory/v1/customers/{customer_id}?organization_id={ORG_ID}"
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }
    print(f">> Ophalen klant-email voor customer_id: {customer_id}")
    response = requests.get(url, headers=headers)
    print(">> Klant-email response:", response.status_code, response.text)
    if response.status_code == 200:
        return response.json().get("customer", {}).get("email", "")
    return ""

@app.route("/order", methods=["GET"])
def get_order():
    email = request.args.get("email")
    order_id = request.args.get("order_id")

    print(f">> Ontvangen verzoek: email={email}, order_id={order_id}")

    if not email or not order_id:
        print(">> Mislukt: ontbrekende parameters")
        return jsonify({"error": "email and order_id required"}), 400

    token = get_access_token()
    if not token:
        print(">> Geen access token ontvangen")
        return jsonify({"error": "Failed to obtain access token"}), 500

    headers = {
        "Authorization": f"Zoho-oauthtoken {token}"
    }

    url = f"https://www.zohoapis.eu/inventory/v1/salesorders?organization_id={ORG_ID}&search_text={order_id}"
    print(f">> Order opzoeken met URL: {url}")
    response = requests.get(url, headers=headers)
    print(">> Orders response:", response.status_code, response.text)

    if response.status_code != 200:
        return jsonify({"error": "Failed to retrieve order data", "details": response.text}), 500

    orders = response.json().get("salesorders", [])
    print(f">> Aantal gevonden orders: {len(orders)}")

    for order in orders:
        customer_id = order.get("customer_id")
        customer_email = get_customer_email(customer_id, token)

        print(f">> Vergelijken: opgegeven email={email.strip().lower()} vs klant-email={customer_email.strip().lower()}")
        if customer_email.strip().lower() == email.strip().lower():
            print(">> Match gevonden, order wordt geretourneerd")
            return jsonify({
                "order_id": order.get("salesorder_number"),
                "date": order.get("date"),
                "status": order.get("status"),
                "total": order.get("total")
            })

    print(">> Geen match gevonden, e-mail komt niet overeen")
    return jsonify({"message": "Geen bestelling gevonden met deze gegevens."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
