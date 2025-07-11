import os
import json
import gspread
from flask import Flask, request, jsonify
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# Setup credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
print("📜 RAW JSON ENV (First 200 chars):")
print(repr(raw_json[:200]))

try:
    creds_dict = json.loads(raw_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Heart").worksheet("Sheet1")
    print("✅ Google Sheet connected successfully.")
except Exception as e:
    print("❌ Failed to connect to Google Sheet:", str(e))
    sheet = None

@app.route("/check", methods=["POST"])
def check_license():
    if not sheet:
        return jsonify({"status": "error", "message": "Sheet not loaded"}), 500

    try:
        data = sheet.get_all_records()
        license_key = request.json.get("license_key", "").strip()

        print("🔐 License key received:", repr(license_key))

        for row in data:
            sheet_key = row.get("LicenseKey", "").strip()
            print("📄 Row Key:", repr(sheet_key))

            if sheet_key == license_key:
                expiry = row.get("ExpiryDate", "")
                if expiry:
                    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                    return jsonify({"status": "valid", "expiry": str(expiry_date)})

        return jsonify({"status": "invalid"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run()
