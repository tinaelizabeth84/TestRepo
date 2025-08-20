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

        github = Github(GITHUB_TOKEN)
        repo = github.get_repo(GITHUB_REPO)

        # PR body template
        pr_body = f"""
### Jira Issue
- **Key:** {issue_key}
- **Summary:** {summary}
- **Reporter:** {reporter}

**Description:**  
{description}
"""

        # --- Check if PR already exists ---
        existing_pr = None
        pulls = repo.get_pulls(state="open")
        for pr in pulls:
            if issue_key in pr.title:
                existing_pr = pr
                break

        if existing_pr:
            # Update PR body if it already exists
            existing_pr.edit(title=f"[{issue_key}] {summary}", body=pr_body)
            print(f"✏️ Updated existing PR: {existing_pr.html_url}")
            return jsonify({"message": "PR updated", "pr_url": existing_pr.html_url}), 200
        else:
            # --- Create branch for new PR ---
            base_branch = repo.default_branch
            source = repo.get_branch(base_branch)
            new_branch_name = f"jira-{issue_key.lower()}"

            # Create branch if it doesn't exist
            try:
                repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=source.commit.sha)
                print(f"✅ Created branch {new_branch_name}")
            except Exception as e:
                print(f"⚠️ Branch may already exist: {e}")

            # Add dummy file for PR
            file_path = f"jira/{issue_key}.md"
            file_content = f"# {issue_key}\n\nSummary: {summary}\nReporter: {reporter}\nDescription:\n{description}"
            try:
                repo.create_file(file_path, f"Add {issue_key} details", file_content, branch=new_branch_name)
                print(f"✅ Added file for PR branch {new_branch_name}")
            except Exception as e:
                print(f"⚠️ File may already exist: {e}")

            # Create Draft PR
            pr = repo.create_pull(
                title=f"[{issue_key}] {summary}",
                body=pr_body,
                head=new_branch_name,
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
    return "✅ Flask Jira Webhook Receiver with PR creation/update is running!", 200


if __name__ == '__main__':
    # Port will be set by Render automatically
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
