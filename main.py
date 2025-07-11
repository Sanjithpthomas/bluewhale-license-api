from flask import Flask
from calculate_api import calculate_bp  # use correct filename here

app = Flask(__name__)
app.register_blueprint(calculate_bp)

@app.route("/")
def home():
    return "Bluewhale Calc API is Running"

if __name__ == "__main__":
    app.run(debug=True)
