import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, jsonify
from calculate_api import calculate_bp
from datetime import datetime

app = Flask(__name__)
app.register_blueprint(calculate_bp)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ✅ Load credentials from environment variable
raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
print("===== RAW JSON from ENV (first 200 chars) =====")
print(repr(raw_json[:200]))
print("================================================")

try:
    service_account_info = json.loads(raw_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Heart").worksheet("Sheet1")
except Exception as e:
    print("❌ ERROR while loading credentials or sheet:", e)
    sheet = None  # prevent crashing, respond in route

@app.route("/check", methods=["POST"])
def check():
    license_key = request.json.get("license_key", "").strip()
    print("Received license key:", repr(license_key))

    if not license_key:
        return jsonify({"status": "error", "message": "License key missing"}), 400

    if sheet is None:
        return jsonify({"status": "error", "message": "Sheet not available"}), 500

    try:
        data = sheet.get_all_records()
        for row in data:
            sheet_key = row.get("LicenseKey", "").strip()
            print("Checking row:", row)
            print("→ Sheet Key:", repr(sheet_key))
            print("→ Input Key:", repr(license_key))

            if sheet_key == license_key:
                expiry = row.get("ExpiryDate")
                if expiry:
                    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                    return jsonify({"status": "valid", "expiry": str(expiry_date)})
        return jsonify({"status": "invalid", "message": "License key not found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": f"Validation failed: {e}"}), 500

# Local run
if __name__ == "__main__":
    app.run()
