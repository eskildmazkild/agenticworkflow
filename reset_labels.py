"""
Reset all story labels back to spec-approved.
Removes: in-progress, in-review
Adds:    spec-approved (if missing)

Usage: python3 reset_labels.py
"""
from config import Config
from github_client import GitHubClient

config = Config.load()
gh = GitHubClient(config)

issues = gh.repo.get_issues(labels=["user-story"], state="open")

for issue in issues:
    label_names = {l.name for l in issue.labels}
    changed = False

    for remove in ["in-progress", "in-review"]:
        if remove in label_names:
            issue.remove_from_labels(remove)
            changed = True

    if "spec-approved" not in label_names:
        issue.add_to_labels("spec-approved")
        changed = True

    status = "✓ reset" if changed else "– already ok"
    print(f"  {status}: #{issue.number} {issue.title}")

print("\nDone!")
