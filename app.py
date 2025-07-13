import os
import json
import gspread
from flask import Flask, request, jsonify
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np

app = Flask(__name__)

# === Google Sheet Setup ===
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

# === License Endpoint ===
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

# === Calculation Endpoint ===
@app.route("/calculate", methods=["POST"])
def calculate_levels():
    try:
        data = request.get_json()
        symbol = data.get("symbol")
        reference_price = float(data.get("reference_price"))
        date_str = data.get("date")
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Fetch 10 previous closes before the selected date
        end_date = target_date - timedelta(days=1)
        start_date = end_date - timedelta(days=30)

        df = yf.download(symbol, start=start_date, end=end_date + timedelta(days=1), interval="1d", progress=False)
        if df.empty or 'Close' not in df.columns:
            return jsonify({"error": "Failed to fetch price data"}), 400

        closes = df['Close'].dropna().tail(10)
        if len(closes) < 10:
            return jsonify({"error": "Insufficient data for calculation"}), 400

        variance = float(np.var(closes))
        volatility = float(np.std(closes))

        # Trend levels based on reference price and volatility
        uptrend = []
        downtrend = []

        for i in range(1, 9):
            up = reference_price + i * volatility
            down = reference_price - i * volatility

            label_up = f"Target {i}"
            label_down = f"Target {i}"

            if i == 3:
                label_up += " (Reversal zone 1)"
                label_down += " (Reversal zone 1)"
            elif i == 4:
                label_up += " (Reversal zone 2)"
                label_down += " (Reversal zone 2)"

            uptrend.append((label_up, round(up, 2)))
            downtrend.append((label_down, round(down, 2)))

        return jsonify({
            "uptrend": uptrend,
            "downtrend": downtrend,
            "variance": round(variance, 4),
            "volatility": round(volatility, 4)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === App Runner ===
if __name__ == "__main__":
    app.run()
