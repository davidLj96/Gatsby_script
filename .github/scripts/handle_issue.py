import os
import requests
from github import Github
from scan_files import get_usage_info

def get_label(repo, label_name, color):
    try:
        return repo.get_label(label_name)
    except Exception:
        return repo.create_label(label_name, color)

token = os.environ['TOKEN']
repo_name = os.environ['GITHUB_REPOSITORY']
gh = Github(token)
repo = gh.get_repo(repo_name)
commit_sha = repo.get_branch('main').commit.sha

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

url = f"https://api.github.com/repos/{repo_name}/dependabot/alerts"
response = requests.get(url, headers=headers)
response.raise_for_status()
alerts = response.json()
dependencies = set()
severities = {}

for alert in alerts:
    if alert['state'] == 'open':
        dependency = alert['security_vulnerability']['package']['name']
        dependencies.add(dependency)
        severities[dependency] = alert['security_vulnerability']['severity']

dependencies = list(dependencies)

issue_title = "Vulnerable Dependencies"
issue_body = f"{get_usage_info(dependencies, repo_name, commit_sha, severities)}"

existing_issues = repo.get_issues(state="open", labels=["Dependabot"])

# Check if an issue for this alert already exists.
issue_exists = False
for issue in existing_issues:
    if issue.title == issue_title and len(dependencies) > 0:
        issue.edit(body=issue_body)
        issue_exists = True
        break

    elif issue.title == issue_title:
        body = 'Dependencies has been resolved.'
        issue.edit(state="closed", body=body)
        issue_exists = True
        break

if not issue_exists and len(dependencies) > 0:
    label = get_label(repo, "Dependabot", "FFA500")
    repo.create_issue(title=issue_title, body=issue_body, labels=[label])

