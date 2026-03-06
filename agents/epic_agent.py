"""
Epic Agent - expands a PO's brief epic outline into a full epic document
with user story list, success metrics, scope, and technical risks.
"""
import json
import re
from anthropic import Anthropic
from config import Config

# Max retries handles 529 overloaded errors automatically with exponential backoff

EPIC_SYSTEM_PROMPT = """You are a Senior Product Owner and Business Analyst working on a React/TypeScript frontend with a REST API backend (web application).

Your job is to take a brief epic outline from a PO and produce a comprehensive epic specification document that enables spec-driven development.

The document must be precise and actionable — it will be used by other agents to write detailed user stories, technical specs, and test cases. Be thorough but concise. No fluff.

Always write in English unless the PO's outline is in Danish, in which case write in Danish.
"""

EPIC_EXPAND_PROMPT = """
Epic title: {title}

PO's outline:
{outline}

Expand this into a full epic specification document using EXACTLY this markdown structure:

# {title}

## Problem Statement
[What problem does this solve? Who experiences it? What is the business impact?]

## Goal
[What does success look like? 1-3 sentences.]

## Success Metrics
- [Measurable metric 1]
- [Measurable metric 2]
- [Measurable metric 3]

## Scope

### In Scope
- [What this epic includes]

### Out of Scope
- [What is explicitly excluded — prevents scope creep]

## User Personas
| Persona | Role | Key Need |
|---------|------|----------|
| [name] | [role] | [what they need from this epic] |

## User Stories
List the user stories that together fulfill this epic. Each story must be small and independently deliverable.
Format each story as a numbered list with title only — the full stories will be written separately.

1. [Story title]
2. [Story title]
3. [Story title]
...

Rules for story breakdown:
- Aim for 5-10 stories — prefer more smaller stories over fewer large ones
- Each story should touch at most 3-4 files and represent 1-2 days of work
- Split every CRUD feature into separate stories: one for listing, one for creating, one for editing, one for deleting
- Separate backend (API/database) from frontend (UI) if each is substantial on its own
- Each story title must start with a verb (e.g. "View", "Create", "Edit", "Delete", "Search", "Display", "Add", "Remove")

## Technical Risks & Considerations
- [Risk or consideration 1]
- [Risk or consideration 2]

## Dependencies
- [External system, API, team, or prerequisite — or "None" if none]

## Definition of Done (Epic Level)
- [ ] All user stories completed and accepted
- [ ] End-to-end tests passing
- [ ] [Add 2-3 epic-specific DoD items]
"""

EPIC_REVISE_PROMPT = """
Here is the current epic specification:

{current_doc}

---

The reviewer has the following feedback:
{feedback}

Please revise the epic specification accordingly. Return the complete updated document, keeping the same markdown structure. Only change what the feedback addresses.
"""

EXTRACT_STORIES_PROMPT = """
Given this epic specification, extract the list of user story titles from the "## User Stories" section.

Epic specification:
{epic_doc}

Return ONLY a JSON array of story title strings, nothing else. Example:
["View dashboard overview", "Create new project", "Edit project settings"]
"""


class EpicAgent:
    def __init__(self, config: Config):
        self.client = Anthropic(api_key=config.anthropic_api_key, max_retries=5)
        self.model = config.claude_model

    def _call(self, system: str, user: str) -> str:
        """Make a single call to Claude and return the text response."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text.strip()

    def expand_epic(self, title: str, outline: str) -> str:
        """Take a PO's brief outline and produce a full epic spec document."""
        prompt = EPIC_EXPAND_PROMPT.format(title=title, outline=outline)
        return self._call(EPIC_SYSTEM_PROMPT, prompt)

    def revise_epic(self, current_doc: str, feedback: str) -> str:
        """Revise an epic document based on reviewer feedback."""
        prompt = EPIC_REVISE_PROMPT.format(current_doc=current_doc, feedback=feedback)
        return self._call(EPIC_SYSTEM_PROMPT, prompt)

    def extract_story_titles(self, epic_doc: str) -> list[str]:
        """
        Extract the list of user story titles from the epic document.
        Returns a list of story title strings.
        """
        prompt = EXTRACT_STORIES_PROMPT.format(epic_doc=epic_doc)
        raw = self._call(EPIC_SYSTEM_PROMPT, prompt)

        # Clean up: strip markdown code fences if present
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw)
        raw = raw.strip()

        try:
            titles = json.loads(raw)
            if isinstance(titles, list):
                return [str(t).strip() for t in titles if t]
        except json.JSONDecodeError:
            # Fallback: parse numbered list from epic doc directly
            pass

        # Fallback: extract from "## User Stories" section in the doc
        stories_section = re.search(
            r"## User Stories\s*(.*?)(?=\n##|\Z)", epic_doc, re.DOTALL
        )
        if stories_section:
            lines = stories_section.group(1).strip().split("\n")
            titles = []
            for line in lines:
                match = re.match(r"^\d+\.\s+(.+)", line.strip())
                if match:
                    titles.append(match.group(1).strip())
            return titles

        return []
