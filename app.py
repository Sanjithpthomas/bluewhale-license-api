from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Replace this with your actual published Google Sheet CSV link
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1WlPAkDRvKVEt-j_Ae4C7dJGmKheEdq35i7Ih1BP-Fco/edit?usp=sharing"

@app.route("/validate", methods=["POST"])
def validate():
    key = request.json.get("license_key", "").strip()
    if not key:
        return jsonify({"status": "error", "message": "No key provided"}), 400

    try:
        df = pd.read_csv(SHEET_CSV_URL)
        row = df[df["LicenseKey"].str.strip() == key]

        if row.empty:
            return jsonify({"status": "invalid", "message": "Invalid license"}), 401

        expiry = pd.to_datetime(row.iloc[0]["ExpiryDate"]).date()
        today = pd.Timestamp.now().date()

        if today > expiry:
            return jsonify({"status": "expired", "expiry": str(expiry)}), 403

        return jsonify({"status": "valid", "expiry": str(expiry)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run()
