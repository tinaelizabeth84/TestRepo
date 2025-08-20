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

        # Extract Jira ticket details
        issue = data.get("issue", {})
        issue_key = issue.get("key", "N/A")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "N/A")
        description = fields.get("description", "N/A")
        reporter = fields.get("reporter", {}).get("displayName", "N/A")

        print(f"🔔 Jira Webhook received: {issue_key} - {summary}")

        if not (GITHUB_TOKEN and GITHUB_REPO):
            return jsonify({"error": "GitHub config missing"}), 500

        github = Github(GITHUB_TOKEN)
        repo = github.get_repo(GITHUB_REPO)

        # Search for an existing PR with the Jira key in the title
        existing_pr = None
        pulls = repo.get_pulls(state="open")
        for pr in pulls:
            if issue_key in pr.title:
                existing_pr = pr
                break

        # PR body template
        pr_body = f"""
### Jira Issue
- **Key:** {issue_key}
- **Summary:** {summary}
- **Reporter:** {reporter}

**Description:**  
{description}
"""

        if existing_pr:
            # Update the existing PR
            existing_pr.edit(title=f"[{issue_key}] {summary}", body=pr_body)
            print(f"✏️ Updated existing PR: {existing_pr.html_url}")
            return jsonify({"message": "PR updated", "pr_url": existing_pr.html_url}), 200
        else:
            # Create a new Draft PR (empty, no code changes)
            base_branch = repo.default_branch
            pr = repo.create_pull(
                title=f"[{issue_key}] {summary}",
                body=pr_body,
                head=base_branch,
                base=base_branch,
                draft=True
            )
            print(f"✅ Created new PR: {pr.html_url}")
            return jsonify({"message": "New PR created", "pr_url": pr.html_url}), 201

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/')
def index():
    return "✅ Flask Jira Webhook Receiver with PR update support is running!", 200
