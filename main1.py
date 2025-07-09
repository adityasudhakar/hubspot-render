from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Root route working"

@app.route("/ping", methods=["POST"])
def ping():
    data = request.json
    print("📡 Received /ping POST")
    print("Payload:", data)
    return {"message": "pong"}, 200

if __name__ == "__main__":
    app.run(debug=True)
