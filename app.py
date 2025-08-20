import os
from flask import Flask, request, jsonify
from github import Github

app = Flask(__name__)

# Load GitHub token and repo from environment
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")

@app.route('/jira-webhook', methods=['POST'])
def jira_webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        # Safely extract Jira ticket details
        issue = data.get("issue", {})
        issue_key = issue.get("key", "N/A")
        fields = issue.get("fields", {})

        summary = fields.get("summary", "N/A")
        description = fields.get("description", "No description provided")
        reporter = fields.get("reporter", {}).get("displayName", "Unknown")

        print(f"🔔 Jira Webhook received: {issue_key} - {summary}")

        if not (GITHUB_TOKEN and GITHUB_REPO):
            return jsonify({"error": "GitHub config missing"}), 500
