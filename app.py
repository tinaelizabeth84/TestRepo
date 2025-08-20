from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/jira-webhook', methods=['POST'])
def jira_webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        # Extract useful fields
        issue = data.get("issue", {})
        issue_key = issue.get("key", "N/A")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "N/A")
        status = fields.get("status", {}).get("name", "N/A")
        reporter = fields.get("reporter", {}).get("displayName", "N/A")

        # Log ticket details (Render will capture logs)
        print("🔔 Jira Webhook received:")
        print(f"   Issue: {issue_key}")
        print(f"   Summary: {summary}")
        print(f"   Status: {status}")
        print(f"   Reporter: {reporter}")

        return jsonify({"message": "Webhook received", "issue": issue_key}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/')
def index():
    return "✅ Flask Jira Webhook Receiver is running!", 200


if __name__ == '__main__':
    # For local dev, Render will override port automatically
    app.run(host='0.0.0.0', port=5000)
