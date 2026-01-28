from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"message": "Hello from Flask backend!", "service": "flask-app"})


if __name__ == "__main__":
    # For local testing only; in production use gunicorn/pm2/systemd
    app.run(host="0.0.0.0", port=5000, debug=True)

