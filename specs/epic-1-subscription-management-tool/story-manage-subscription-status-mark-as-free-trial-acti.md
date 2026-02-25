<!-- GitHub Issue: #5 -->
<!-- Part of Epic: #1 -->

# Manage subscription status — mark as Free Trial, Active, or Cancelled with relevant dates

## User Story
As Alex (an individual managing personal subscriptions), I want to set and update the status of each subscription — Free Trial, Active, or Cancelled — with the relevant associated dates, so that I always have an accurate, up-to-date picture of which services I'm paying for, which are in trial, and which I have already cancelled.

## Background
Users frequently lose track of subscription states: a free trial silently converts to a paid subscription, or a cancelled service is forgotten with an unknown end date. Without structured status management tied to specific dates, the dashboard cannot accurately reflect real costs or warn users about impending transitions. This story establishes the status state machine that underpins the entire subscription overview.

---

## Acceptance Criteria

### AC-1: Display and select status in the subscription form
**Given** a user is creating or editing a subscription  
**When** the status field is rendered  
**Then** exactly three options are available — `Active`, `Free Trial`, and `Cancelled` — presented as a segmented control or radio group, with the current status pre-selected when editing an existing subscription

---

### AC-2: Mark a subscription as Active
**Given** a user is creating or editing a subscription  
**When** the user selects `Active` as the status and saves the form  
**Then** the subscription is saved with status `Active`, only the `Start Date` date field is required and stored, and no trial end date or cancellation date fields are displayed or persisted

---

### AC-3: Mark a subscription as Free Trial with a required trial end date
**Given** a user is creating or editing a subscription  
**When** the user selects `Free Trial` as the status  
**Then** a `Trial End Date` date field becomes visible and required; when the user saves, the subscription is persisted with status `Free Trial` and the provided trial end date; if the `Trial End Date` is left empty or is on or before the `Start Date`, a validation error is shown and the form cannot be submitted

---

### AC-4: Mark a subscription as Cancelled with required cancellation date and last active date
**Given** a user is creating or editing a subscription  
**When** the user selects `Cancelled` as the status  
**Then** a `Cancellation Date` field and a `Last Active Date` field both become visible and required; when saved, the subscription is persisted with status `Cancelled` and both dates; if either date is missing, if `Cancellation Date` is before `Start Date`, or if `Last Active Date` is after `Cancellation Date`, a field-level validation error is shown and the form cannot be submitted

---

### AC-5: Enforce valid status transitions on existing subscriptions
**Given** a subscription already exists with a given status  
**When** the user changes the status to a new value  
**Then** the following transitions are permitted: `Active → Cancelled`, `Active → Free Trial`, `Free Trial → Active`, `Free Trial → Cancelled`, `Cancelled → Active`; in all cases the previously inapplicable date fields are cleared, and the newly required date fields become mandatory before the form can be saved

> **Note:** `Cancelled → Free Trial` is disallowed. If a user attempts this transition, an inline error message is displayed: *"A cancelled subscription cannot be moved back to Free Trial. Set it to Active first."* and the status selection reverts to `Cancelled`.

---

### AC-6: Reflect status visually and contextually on the subscription list and detail view
**Given** a subscription has been saved with any of the three statuses  
**When** the subscription is rendered in the list or detail view  
**Then**:
- `Active` subscriptions display a green status badge
- `Free Trial` subscriptions display an amber/yellow badge plus the formatted `Trial End Date` (e.g. *"Trial ends 15 Aug 2025"*)
- `Cancelled` subscriptions display a grey/red badge, are visually dimmed, and show the `Last Active Date` (e.g. *"Last active 01 Jun 2025"*)

---

### AC-7: Cancelled subscriptions are excluded from cost totals
**Given** one or more subscriptions have status `Cancelled`  
**When** the dashboard calculates monthly and yearly cost totals (per category and in aggregate)  
**Then** cancelled subscriptions contribute `£0` to all cost totals; `Active` and `Free Trial` subscriptions are both included in cost totals

---

## Tasks

- [ ] **Backend:** Define and document the status state machine — permitted transitions, forbidden transitions (`Cancelled → Free Trial`), and which date fields are required per status — in a shared validation schema (e.g. Zod schema or equivalent) usable by both API and frontend
- [ ] **Backend:** Update the `PATCH /api/subscriptions/:id` endpoint to validate status transitions server-side, enforce date business rules (trial end date after start date; cancellation date after start date; last active date on or before cancellation date), return structured `400` validation errors per field, and clear inapplicable date fields when status changes
- [ ] **Backend:** Update the `POST /api/subscriptions` endpoint with the same status/date validation rules for the creation case
- [ ] **Frontend:** Build a `SubscriptionStatusControl` component — segmented control or radio group rendering the three status options — that conditionally renders the correct date input fields (`Trial End Date` for Free Trial; `Cancellation Date` + `Last Active Date` for Cancelled) with visible required indicators
- [ ] **Frontend:** Implement client-side validation logic (mirroring the shared Zod schema) in the subscription form: enforce required date fields per status, enforce date ordering rules, block the forbidden `Cancelled → Free Trial` transition with an inline error message, and clear stale date values when switching status
- [ ] **Frontend:** Update the subscription list item and detail view components to render the correct status badge (colour + label) and the relevant contextual date string per status
- [ ] **Frontend:** Update the dashboard cost aggregation logic to exclude `Cancelled` subscriptions from all totals
- [ ] **Tests:** Write integration tests for `POST` and `PATCH` endpoints covering: each valid status + required dates, missing required dates per status, invalid date ordering, and the forbidden `Cancelled → Free Trial` transition

---

## Test Cases

### TC-1: Status options are rendered correctly in the form
- **Type:** E2E
- **Setup:** Navigate to the "Add Subscription" form; separately, navigate to "Edit" for an existing subscription with status `Free Trial`
- **Steps:**
  1. Open the "Add Subscription" form
  2. Inspect the status control
  3. Open the "Edit" form for a `Free Trial` subscription
  4. Inspect the status control pre-selection
- **Expected Result:** Exactly three options (`Active`, `Free Trial`, `Cancelled`) are present in both forms; the edit form pre-selects `Free Trial`

---

### TC-2: Save subscription as Active stores only start date
- **Type:** Integration
- **Setup:** Authenticated session; a valid subscription payload with `status: "active"`, `startDate: "2025-01-01"`, no `trialEndDate` or `cancellationDate`
- **Steps:**
  1. `POST /api/subscriptions` with the payload
  2. Read back the created record
- **Expected Result:** Response is `201`; persisted record has `status: "active"`, `startDate: "2025-01-01"`, `trialEndDate: null`, `cancellationDate: null`, `lastActiveDate: null`

---

### TC-3: Free Trial requires trial end date after start date
- **Type:** Integration
- **Setup:** Authenticated session; payloads prepared for: (a) missing `trialEndDate`, (b) `trialEndDate` equal to `startDate`, (c) `trialEndDate` before `startDate`, (d) valid `trialEndDate` after `startDate`
- **Steps:**
  1. `POST /api/subscriptions` with payload (a) — missing trial end date
  2. `POST /api/subscriptions` with payload (b) — trial end date equals start date
  3. `POST /api/subscriptions` with payload (c) — trial end date before start date
  4. `POST /api/subscriptions` with payload (d) — valid dates
- **Expected Result:** Requests (a), (b), (c) return `400` with a field-level error on `trialEndDate`; request (d) returns `201`

---

### TC-4: Cancelled status requires both dates with valid ordering
- **Type:** Integration
- **Setup:** Authenticated session; payloads: (a) missing `cancellationDate`, (b) missing `lastActiveDate`, (c) `cancellationDate` before `startDate`, (d) `lastActiveDate` after `cancellationDate`, (e) all dates valid and correctly ordered
- **Steps:**
  1. Submit each payload via `POST /api/subscriptions`
- **Expected Result:** Payloads (a)–(d) return `400` with field-level errors identifying the specific invalid field; payload (e) returns `201`

---

### TC-5: Forbidden transition Cancelled → Free Trial is rejected
- **Type:** Integration
- **Setup:** An existing subscription with `status: "cancelled"` in the database
- **Steps:**
  1. `PATCH /api/subscriptions/:id` with `{ "status": "free_trial", "trialEndDate": "2025-12-01" }`
- **Expected Result:** Response is `422` (or `400`) with error message indicating the transition from `Cancelled` to `Free Trial` is not permitted; subscription status remains `cancelled` in the database

---

### TC-6: Status badges and contextual dates render correctly in the list
- **Type:** E2E
- **Setup:** Three subscriptions seeded in the system — one `Active` (start date 2025-01-01), one `Free Trial` (trial end date 2025-08-15), one `Cancelled` (last active date 2025-06-01)
- **Steps:**
  1. Navigate to the subscription list
  2. Locate each of the three subscriptions
  3. Inspect badge colour, label, and contextual date string for each
- **Expected Result:**
  - `Active` subscription shows a green badge labelled "Active" with no trial or cancellation date
  - `Free Trial` subscription shows an amber badge labelled "Free Trial" and the text "Trial ends 15 Aug 2025"
  - `Cancelled` subscription shows a grey/red badge labelled "Cancelled", is visually dimmed, and shows "Last active 01 Jun 2025"

---

### TC-7: Cancelled subscriptions excluded from dashboard cost totals
- **Type:** E2E / Integration
- **Setup:** Two `Active` subscriptions (£10/month and £20/month) and one `Cancelled` subscription (£15/month), all in the same category
- **Steps:**
  1. Navigate to the dashboard
  2. Read the monthly total for the category
  3. Read the overall monthly total
- **Expected Result:** Both the category total and the overall monthly total equal £30; the £15 cancelled subscription is not included in any total

---

## Technical Notes

- **API endpoints involved:**
  - `POST /api/subscriptions` — creation with status and date validation
  - `PATCH /api/subscriptions/:id` — update with transition validation and date clearing
  - `GET /api/subscriptions` — must return all status and date fields for frontend rendering
- **State machine definition:** The permitted transitions should be defined as a single source-of-truth constant (e.g. `ALLOWED_TRANSITIONS` map) importable by both the backend validation layer and the frontend form logic to prevent drift
- **Date field clearing:** When status changes (e.g. `Free Trial → Active`), the backend must explicitly set inapplicable date fields to `null` to avoid stale data persisting silently
- **Frontend form state:** Use a controlled form approach (e.g. React Hook Form + Zod resolver); the status field change should trigger a reset of the conditional date fields to `undefined`/empty to prevent old values being submitted
- **Cost aggregation sync:** The dashboard total selector/hook must filter on `status !== "cancelled"` — this logic should be unit-tested independently from the UI rendering
- **Date display format:** Dates should be formatted consistently across the app (e.g. `DD MMM YYYY`) using a single utility function to avoid locale inconsistencies

---

## Story Points
**Estimate:** 5 points  
**Reasoning:** The conditional field logic, state machine enforcement (including the forbidden transition), cross-field date validation on both client and server, and the visual status rendering across multiple views represent moderate-to-high complexity across the full stack, though no new infrastructure is required.

---

## Definition of Done
- [ ] All Acceptance Criteria verified manually against the running application
- [ ] All Test Cases (TC-1 through TC-7) automated and passing in CI
- [ ] Code reviewed and approved by at least one other developer
- [ ] No console errors or TypeScript errors (`tsc --noEmit` passes cleanly)
- [ ] The status state machine constant is defined in a single shared location and imported by both backend and frontend — no duplicated transition logic
- [ ] All date validation rules (ordering, required fields per status) are covered by backend integration tests with explicit assertions on error field names returned in `400` responses