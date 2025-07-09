from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

API_KEY = "vn-96862437e7034ebeb1082c45e0181caf"
USER_EMAIL = "adi@vanna.ai"

USAGE_SYSTEM_PROMPT = (
    "Always include a column named 'email' for the user's email address. "
    "Also show number of questions asked, duration (days between signup and last question) "
    "and recency (days between last question and today)."
)

HUBSPOT_SYSTEM_PROMPT = (
    "Always include a column named 'email' for the user's email address "
    "and use 'lastmodifieddate' for day or date or duration calculations."
)

def extract_emails_from_payload(payload):
    emails = []
    for row in payload["json_table"]["data"]:
        for key in row:
            if key.lower() == "email":
                emails.append(row[key])
    return emails

def call_vanna_agent(agent_id, message):
    try:
        response = requests.post(
            "https://app.vanna.ai/api/v0/chat_sse",
            headers={
                "Content-Type": "application/json",
                "VANNA-API-KEY": API_KEY
            },
            data=json.dumps({
                "message": message,
                "user_email": USER_EMAIL,
                "agent_id": agent_id,
                "acceptable_responses": ["dataframe", "text"]
            }),
            stream=True
        )
        result = {"text": "", "dataframe": []}
        for line in response.iter_lines():
            if line and line.decode("utf-8").startswith("data:"):
                payload = json.loads(line.decode("utf-8")[5:].strip())
                if payload.get("type") == "text":
                    result["text"] += payload["text"] + "\n"
                elif payload.get("type") == "dataframe":
                    result["dataframe"] = payload["json_table"]["data"]
        return result
    except Exception as e:
        print("❌ Error in call_vanna_agent:", e)
        return None

@app.route("/query", methods=["POST"])
def handle_query():
    print("🟢 Received POST /query request")  # Optional debug print
    data = request.json
    print("Payload:", data)

    flow = data.get("flow")
    query = data.get("query")

    if flow == "1":
        message_1 = f"{query} {USAGE_SYSTEM_PROMPT}"
        resp_1 = call_vanna_agent("hosted-app-usage", message_1)
        if not resp_1 or "dataframe" not in resp_1:
            return jsonify({"error": "Vanna did not return any data"}), 500
        emails = extract_emails_from_payload({"json_table": {"data": resp_1["dataframe"]}})
        if not emails:
            return jsonify({"error": "No emails found."}), 400
        message_2 = f"show me email address and lastmodifieddate for: {', '.join(emails)}"
        resp_2 = call_vanna_agent("vanna-hubspot", message_2)
        return jsonify({
            "step_1": resp_1,
            "step_2": resp_2
        })

    elif flow == "2":
        message_1 = f"{query} {HUBSPOT_SYSTEM_PROMPT}"
        resp_1 = call_vanna_agent("vanna-hubspot", message_1)
        emails = extract_emails_from_payload({"json_table": {"data": resp_1["dataframe"]}})
        if not emails:
            return jsonify({"error": "No emails found."}), 400
        message_2 = (
            f"For the following users, return number of questions asked, duration "
            f"(days between signup and last question) and recency (days between last question and today): {', '.join(emails)}"
        )
        resp_2 = call_vanna_agent("hosted-app-usage", message_2)
        return jsonify({
            "step_1": resp_1,
            "step_2": resp_2
        })

    return jsonify({"error": "Invalid flow"}), 400

if __name__ == "__main__":
    app.run(debug=True)