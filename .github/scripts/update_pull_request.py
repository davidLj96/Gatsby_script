import os
import re
from github import Github
from scan_files import get_usage_info

# dependencies = ['express', 'react', 'fs']
# repo_name = 'davidLj96/degree_project'
# commit_sha = 'aassssdafko13fko293jf'
access_token = os.environ['TOKEN']
repo_name = os.environ['REPOSITORY']
pr_number = int(os.environ['PULL_REQUEST'])

g = Github(access_token)
repo = g.get_repo(repo_name)
pull_request = repo.get_pull(pr_number)
pull_request_user = pull_request.user.login
commit_sha = repo.get_branch(pull_request.head.ref).commit.sha

# Get the commit associated with the pull request
commit = pull_request.get_commits()[0]

dependencies = set()
# Get the dependencies from the commit message
for line in commit.commit.message.split('\n'):
    if line.startswith('- dependency-name:'):
        dependencies.add(line.split(': ')[1])
# dependency_pattern = r"- dependency-name: (\w+)"
# dependencies = re.findall(dependency_pattern, commit.commit.message)

dependencies = list(dependencies)

description = f'## Dependabot\n{pull_request.body}\n\n## Usabot\n'
description += get_usage_info(dependencies, repo_name, commit_sha)

pull_request.edit(
    body = description
)
