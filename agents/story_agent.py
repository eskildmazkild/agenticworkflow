"""
Story Agent - takes an epic context and a user story title and produces
a complete story specification including: user story, acceptance criteria,
technical tasks, test cases, and definition of done.
"""
from anthropic import Anthropic
from config import Config

STORY_SYSTEM_PROMPT = """You are a Senior Product Owner, Business Analyst, and QA Engineer working on a React/TypeScript frontend with a REST API backend.

Your job is to write complete, precise user story specifications that enable a developer agent to implement features correctly without ambiguity.

Rules:
- Acceptance Criteria must be in Given/When/Then (Gherkin-style) format
- Test Cases must directly correspond to the Acceptance Criteria and be written for automated testing
- Tasks must be technical and specific enough for a developer to estimate and implement
- Identify edge cases and error states — these are the most common sources of bugs
- Always write in English unless the epic context is in Danish

SCOPE RULES (critical — a developer agent implements each story in a single pass):
- Each story must touch AT MOST 3-4 files total (e.g. one API route + one component + one type file)
- Each story should represent AT MOST 1-2 days of developer work (story points 1-3)
- If a story feels large, split it: "Manage subscriptions" → "List subscriptions" + "Add subscription" + "Edit subscription"
- Separate backend and frontend into different stories when they are substantial on their own
- Never combine CRUD operations into one story — each operation (list, create, edit, delete) is its own story
- Aim for 3-5 acceptance criteria maximum — if you need more, the story is too big
"""

STORY_WRITE_PROMPT = """
Epic context:
{epic_doc}

---

Write a complete specification for this user story: "{story_title}"

Use EXACTLY this markdown structure:

# {story_title}

## User Story
As a [persona from the epic], I want to [action], so that [value/outcome].

## Background
[1-3 sentences of context. Why does this story exist? What is the user's current pain?]

## Acceptance Criteria

### AC-1: [Short name for this criterion]
**Given** [initial context / state]
**When** [user action or system event]
**Then** [expected outcome]

### AC-2: [Short name]
**Given** ...
**When** ...
**Then** ...

[Continue for all scenarios. Include: happy path, validation errors, empty states, edge cases. Aim for 4-7 ACs.]

## Tasks
Technical breakdown for the developer. Each task should be a concrete unit of work.

- [ ] **Backend:** [task description] *(e.g., Create POST /api/resource endpoint with validation)*
- [ ] **Backend:** [task description]
- [ ] **Frontend:** [task description] *(e.g., Build ResourceForm component with controlled inputs)*
- [ ] **Frontend:** [task description]
- [ ] **Tests:** [task description] *(e.g., Write integration tests for POST endpoint)*
- [ ] **Tests:** [task description]

[3-8 tasks total]

## Test Cases
Automated test cases corresponding to the Acceptance Criteria above.

### TC-1: [Corresponds to AC-1 — same name]
- **Type:** [Unit | Integration | E2E]
- **Setup:** [Preconditions / test data needed]
- **Steps:**
  1. [Step 1]
  2. [Step 2]
- **Expected Result:** [What should happen]

### TC-2: [Corresponds to AC-2]
- **Type:** ...
- **Setup:** ...
- **Steps:**
  1. ...
- **Expected Result:** ...

[One test case per AC]

## Technical Notes
- [API endpoints involved, if known]
- [State management considerations]
- [Performance considerations if relevant]
- [Security considerations if relevant]

## Story Points
**Estimate:** [1 / 2 / 3 / 5 / 8 / 13] points
**Reasoning:** [One sentence explaining the estimate]

## Definition of Done
- [ ] All Acceptance Criteria verified manually
- [ ] All Test Cases automated and passing
- [ ] Code reviewed and approved
- [ ] No console errors or TypeScript errors
- [ ] [Add 1-2 story-specific DoD items]
"""

STORY_REVISE_PROMPT = """
Here is the current user story specification:

{current_doc}

---

The reviewer has the following feedback:
{feedback}

Please revise the specification accordingly. Return the complete updated document, keeping the same markdown structure. Only change what the feedback addresses.
"""


class StoryAgent:
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

    def write_story(self, epic_context: str, story_title: str) -> str:
        """Write a complete story specification."""
        prompt = STORY_WRITE_PROMPT.format(
            epic_doc=epic_context,
            story_title=story_title,
        )
        return self._call(STORY_SYSTEM_PROMPT, prompt)

    def revise_story(self, current_doc: str, feedback: str) -> str:
        """Revise a story specification based on reviewer feedback."""
        prompt = STORY_REVISE_PROMPT.format(
            current_doc=current_doc,
            feedback=feedback,
        )
        return self._call(STORY_SYSTEM_PROMPT, prompt)
