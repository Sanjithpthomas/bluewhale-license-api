from flask import Blueprint, request, jsonify
import math
import datetime
import yfinance as yf

calculate_bp = Blueprint("calculate", __name__)

def fetch_prices(symbol, current_day):
    end_date = current_day - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=30)
    df = yf.download(symbol, start=start_date, end=end_date + datetime.timedelta(days=1), interval='1d', progress=False)
    close_prices = df['Close'].dropna()
    if len(close_prices) < 10:
        raise ValueError("Not enough historical data.")
    return close_prices.tail(10)

@calculate_bp.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.json
        symbol = data.get("symbol")
        ref_price = float(data.get("reference_price"))
        date_str = data.get("date")  # Optional; format: "YYYY-MM-DD"

        if not symbol or not ref_price:
            return jsonify({"error": "Missing symbol or reference price"}), 400

        if date_str:
            current_day = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            current_day = datetime.datetime.now().date()

        prices = fetch_prices(symbol, current_day)

        log_returns = [math.log(prices.iloc[i] / prices.iloc[i - 1]) for i in range(1, 10)]
        avg_log = sum(log_returns) / len(log_returns)
        avg_sq = sum(x ** 2 for x in log_returns) / len(log_returns)
        variance = avg_sq - avg_log ** 2
        volatility = math.sqrt(variance) * 100
        expected_points = ref_price * volatility / 100

        uptrend = [
            ("BUY/UPTREND starts at", ref_price + expected_points * 0.236),
            ("Target 1", ref_price + expected_points * 0.382),
            ("Target 2", ref_price + expected_points * 0.5),
            ("Target 3 (Reversal zone 1)", ref_price + expected_points * 0.618),
            ("Target 4 (Reversal zone 2)", ref_price + expected_points * 0.786),
            ("Target 5", ref_price + expected_points * 0.888),
            ("Target 6", ref_price + expected_points * 1.236),
            ("Target 7", ref_price + expected_points * 1.618),
        ]

        downtrend = [
            ("SELL/DOWNTREND starts at", ref_price - expected_points * 0.236),
            ("Target 1", ref_price - expected_points * 0.382),
            ("Target 2", ref_price - expected_points * 0.5),
            ("Target 3 (Reversal zone 1)", ref_price - expected_points * 0.618),
            ("Target 4 (Reversal zone 2)", ref_price - expected_points * 0.786),
            ("Target 5", ref_price - expected_points * 0.888),
            ("Target 6", ref_price - expected_points * 1.236),
            ("Target 7", ref_price - expected_points * 1.618),
        ]

        return jsonify({
            "uptrend": [(label, round(val, 2)) for label, val in uptrend],
            "downtrend": [(label, round(val, 2)) for label, val in downtrend],
            "volatility": round(volatility, 4),
            "variance": round(variance, 8),
            "used_date": str(current_day)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@calculate_bp.route("/check", methods=["POST"])
def check_license():
    data = request.json
    key = data.get("key")

    # You can replace this check with actual logic if needed
    if key == "VALIDKEY":
        return jsonify({"status": "valid"})
    else:
        return jsonify({"status": "invalid"})

