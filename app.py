import os
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify
from datetime import datetime

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)


# ✅ Open the Google Sheet named "Heart", then Sheet1
sheet = client.open("Heart").worksheet("Sheet1")

@app.route("/validate", methods=["POST"])
def validate():
    license_key = request.json.get("license_key", "").strip()
    if not license_key:
        return jsonify({"status": "error", "message": "License key missing"}), 400

    data = sheet.get_all_records()

    for row in data:
        if row.get("LicenseKey") == license_key:
            expiry = row.get("ExpiryDate")
            if expiry:
                try:
                    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                    return jsonify({"status": "valid", "expiry": str(expiry_date)})
                except Exception as e:
                    return jsonify({"status": "error", "message": f"Invalid expiry format: {e}"}), 500

    return jsonify({"status": "invalid", "message": "License key not found"}), 404

if __name__ == "__main__":
    app.run()
