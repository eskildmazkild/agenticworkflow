# Spec Agent — Phase 1: Spec Machine

A CLI tool for spec-driven development. Write a brief epic outline as a PO, and the agent produces a complete specification with user stories, acceptance criteria, tasks, and test cases — with a human-in-the-loop review step at each stage.

## What it does

```
PO writes epic outline
        ↓
[Agent] Expands into full epic spec
        ↓
[REVIEW] You review and approve (or give feedback)
        ↓
[Agent] Writes spec for each user story
        ↓
[REVIEW] You review and approve each story
        ↓
[Auto] Creates GitHub Issues + commits spec files to repo
```

Each spec includes:
- User story (As a / I want / So that)
- Acceptance Criteria (Given/When/Then)
- Developer tasks
- Automated test cases (mapped 1:1 to ACs)
- Story points estimate
- Definition of Done

## Setup

### 1. Clone or copy this folder to your machine

```bash
# Navigate to the spec-agent folder
cd spec-agent
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → select `repo` scope |
| `GITHUB_REPO` | Your repo in format `username/repo-name` |
| `GITHUB_BRANCH` | Branch for spec files (default: `main`) |
| `SPECS_FOLDER` | Folder in repo for specs (default: `specs`) |

### 5. Run

```bash
python main.py new-epic
```

## Example session

```
$ python main.py new-epic

╭─ 🤖 Spec Agent ─────────────────────────────╮
│ Spec Agent — Phase 1: Spec Machine           │
│                                              │
│ Flow:                                        │
│   1. You provide a brief epic outline        │
│   2. Agent expands into full epic spec  ← review │
│   3. Agent writes specs for each story  ← review │
│   4. Pushed to GitHub as Issues + files      │
╰──────────────────────────────────────────────╯

Epic title: User Authentication

Enter your outline:
Users need to be able to sign up, log in and log out.
We need email/password auth and possibly Google OAuth later.
Users should stay logged in across sessions.

→ Expanding epic...

━━━ REVIEW POINT 1: Epic Specification ━━━
[full spec rendered in terminal]

Action [y/f/s]: y
✓ Approved

Found 4 user stories:
  1. Register new account
  2. Log in with email and password
  3. Log out and session management
  4. Reset forgotten password

━━━ REVIEW POINT 2.1: Story 1/4 ━━━
→ Writing spec for: Register new account
[full story spec rendered]

Action [y/f/s]: f
Enter feedback:
Add an AC for duplicate email validation

→ Revising... (revision 1)
[revised spec rendered]

Action [y/f/s]: y
✓ Approved

... [continues for each story] ...

━━━ FINAL STEP: Push to GitHub ━━━
Push everything to GitHub? [Y/n]: y

✓ Epic issue created: #42
✓ Story issue created: #43 — Register new account
✓ Story issue created: #44 — Log in with email and password
...
✓ Spec files committed to: specs/epic-42-user-authentication/

╭─ ✅ Done ────────────────────────────────────╮
│ Epic created successfully!                   │
│ Epic issue:  https://github.com/...          │
│ Stories:     4 issues created               │
│ Spec files:  specs/epic-42-.../             │
╰──────────────────────────────────────────────╯
```

## Output structure in your repo

```
specs/
└── epic-42-user-authentication/
    ├── epic.md                          ← Full epic specification
    ├── story-register-new-account.md   ← Story spec with AC + tasks + tests
    ├── story-log-in-with-email.md
    ├── story-log-out-and-session.md
    └── story-reset-forgotten-password.md
```

GitHub Issues:
- `[EPIC] User Authentication` — labelled `epic`, `spec-approved`
- `[STORY] Register new account` — labelled `user-story`, `spec-approved`, linked to epic

## Troubleshooting

**`Missing required environment variables`**
→ Check that `.env` exists and has all three required variables filled in.

**`404` GitHub error**
→ Check `GITHUB_REPO` format is `username/repo-name` (no URL, no trailing slash).

**`401` GitHub error**
→ Your `GITHUB_TOKEN` is invalid or expired. Generate a new one.

**`403` GitHub error**
→ Your token doesn't have `repo` scope. Regenerate with full `repo` access.

**Stories list is empty after epic review**
→ The epic doc needs a `## User Stories` section with a numbered list. Give feedback asking the agent to add one.

## Next phases (coming soon)

- **Phase 2 — Developer Agent:** Picks up a story from the backlog, reads the spec, and implements it in a new branch
- **Phase 3 — Review Agent:** Evaluates PRs against the spec + AC, approves or requests changes, triggers deployment pipeline
