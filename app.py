import os
import sys
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify
from calculate_api import calculate_bp
from datetime import datetime

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ Register blueprint for trend calculation API
app.register_blueprint(calculate_bp)

# ✅ Google Sheets authorization setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ✅ Load credentials from environment variable
service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)

# ✅ Open the Google Sheet named "Heart", then Sheet1
sheet = client.open("Heart").worksheet("Sheet1")

# ✅ License key validation route
@app.route("/check", methods=["POST"])
def check():
    license_key = request.json.get("license_key", "").strip()
    print("Received license key:", repr(license_key))  # 🟢 DEBUG PRINT

    if not license_key:
        return jsonify({"status": "error", "message": "License key missing"}), 400

    try:
        data = sheet.get_all_records()
        for row in data:
            sheet_key = row.get("LicenseKey", "").strip()
            print("Checking row:", row)  # 🟢 DEBUG
            print("Comparing license keys:")
            print("→ From Sheet:", repr(sheet_key))
            print("→ From User :", repr(license_key))

            if sheet_key == license_key:
                expiry = row.get("ExpiryDate")
                if expiry:
                    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                    return jsonify({"status": "valid", "expiry": str(expiry_date)})
        return jsonify({"status": "invalid", "message": "License key not found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": f"Validation failed: {e}"}), 500

# ✅ Run app locally (only used in local testing, Render uses gunicorn)
if __name__ == "__main__":
    app.run()
