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

        # Debug logs
        print("🔔 Jira Webhook received:")
        print(f"   Issue: {issue_key}")
        print(f"   Summary: {summary}")
        print(f"   Reporter: {reporter}")

        # --- GitHub PR Creation ---
        if GITHUB_TOKEN and GITHUB_REPO:
            github = Github(GITHUB_TOKEN)
            repo = github.get_repo(GITHUB_REPO)

            # Create a new branch from default branch (main/master)
            base_branch = repo.default_branch
            source = repo.get_branch(base_branch)
            new_branch_name = f"jira-{issue_key.lower()}"
            try:
                repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=source.commit.sha)
                print(f"✅ Created new branch {new_branch_name}")
            except Exception as e:
                print(f"⚠️ Branch may already exist: {e}")

            # Create a dummy commit file (so PR has changes)
            file_path = f"jira/{issue_key}.md"
            file_content = f"# {issue_key}\n\n**Summary:** {summary}\n\n**Description:** {description}\n\n**Reporter:** {reporter}\n"
            try:
                repo.create_file(file_path, f"Add {issue_key} details", file_content, branch=new_branch_name)
            except Exception as e:
                print(f"⚠️ File may already exist: {e}")

            # Create a Pull Request
            pr_title = f"[{issue_key}] {summary}"
            pr_body = f"""
### Jira Issue
- **Key:** {issue_key}
- **Summary:** {summary}
- **Reporter:** {reporter}

**Description:**  
{description}
"""
            pr = repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=new_branch_name,
                base=base_branch
            )
            print(f"✅ Created PR: {pr.html_url}")

        return jsonify({"message": "Webhook received and PR created", "issue": issue_key}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "✅ Flask Jira Webhook Receiver is running with PR creation!", 200
