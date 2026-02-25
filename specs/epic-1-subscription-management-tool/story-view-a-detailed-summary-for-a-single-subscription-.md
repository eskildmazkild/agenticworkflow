<!-- GitHub Issue: #8 -->
<!-- Part of Epic: #1 -->

# View a detailed summary for a single subscription including full status history and cost breakdown

## User Story
As Alex (or Jordan), I want to view a detailed summary page for a single subscription — including its full status history, cost breakdown by month and year, and all associated metadata — so that I can understand exactly what I am paying, how the subscription's status has changed over time, and make informed decisions about keeping or cancelling it.

## Background
Users managing multiple subscriptions often need more information than what is visible in the list overview. Without a dedicated detail view, they cannot see the full lifecycle of a subscription (e.g. when it transitioned from trial to active, or when it was cancelled), nor can they verify the normalized cost calculations that contribute to their dashboard totals. This story delivers a single source of truth for each individual subscription record.

## Acceptance Criteria

### AC-1: Subscription detail page loads with complete metadata
**Given** a subscription exists in the system with a name, category, cost, billing cycle, start date, and status
**When** the user navigates to the detail page for that subscription (e.g. via clicking it in the subscription list)
**Then** the page displays all subscription metadata: name, category, cost (as entered), billing cycle (monthly or yearly), start date, and current status — with no fields missing or showing placeholder values

### AC-2: Cost breakdown displays monthly and yearly equivalent costs
**Given** a subscription with a specific cost and billing cycle (either monthly or yearly) is being viewed on its detail page
**When** the detail page renders
**Then** the cost section shows:
- The original cost and billing cycle as entered (e.g. "€120 / year")
- The normalized monthly equivalent cost (e.g. "€10.00 / month"), calculated as `yearly cost ÷ 12` for yearly subscriptions or as-is for monthly subscriptions, rounded to 2 decimal places
- The annualized yearly equivalent cost (e.g. "€120.00 / year"), calculated as `monthly cost × 12` for monthly subscriptions or as-is for yearly subscriptions

### AC-3: Status-specific dates are displayed based on current status
**Given** a subscription is being viewed on its detail page
**When** the current status is **Free Trial**
**Then** the status section displays the trial end date alongside the "Free Trial" status label
**And** when the current status is **Cancelled**, the section displays both the cancellation date and the last active date
**And** when the current status is **Active**, no trial or cancellation dates are shown (or they are explicitly labelled as "N/A")

### AC-4: Status history is displayed in chronological order
**Given** a subscription has undergone one or more status transitions (e.g. Trial → Active, or Active → Cancelled)
**When** the user views the detail page
**Then** the status history section lists each recorded status change as a timeline entry with:
- The previous status
- The new status
- The date and time the change was recorded
**And** entries are ordered from most recent to oldest (newest first)
**And** if the subscription has never changed status (only has its initial status), the section displays the initial status with its creation date and a label such as "Initial status"

### AC-5: Subscription with no status history shows a meaningful empty state for history
**Given** a newly created subscription that has not undergone any status transitions
**When** the user views the detail page
**Then** the status history section displays an informational message such as "No status changes recorded yet" or shows the single initial status entry rather than a blank or broken section

### AC-6: Navigating to a non-existent subscription shows an error state
**Given** the user navigates directly to a subscription detail URL for a subscription ID that does not exist (e.g. deleted or invalid ID)
**When** the page attempts to load
**Then** the page displays a clear error message such as "Subscription not found"
**And** a navigation control (e.g. "Back to subscriptions") is shown to allow the user to return to the subscription list
**And** no empty or broken UI elements are rendered

### AC-7: User can navigate from the detail page back to the subscription list and to the edit form
**Given** the user is viewing a subscription's detail page
**When** the page renders
**Then** a "Back" or "All Subscriptions" link/button is visible and navigates to the subscription list when clicked
**And** an "Edit" button is visible and navigates to the subscription's edit form when clicked

## Tasks

- [ ] **Backend:** Create `GET /api/subscriptions/:id` endpoint that returns full subscription metadata including all status-related dates, billing information, and a `statusHistory` array with entries containing `{ fromStatus, toStatus, changedAt }` *(ensure the response model includes all fields required by AC-1 through AC-4)*
- [ ] **Backend:** Ensure status history entries are written to the database whenever a subscription's status changes (in the edit/status-change flow) and are returned sorted by `changedAt` descending from the API
- [ ] **Frontend:** Create a `SubscriptionDetailPage` component (routed at e.g. `/subscriptions/:id`) that fetches subscription data from `GET /api/subscriptions/:id` and renders loading, error (404/other), and success states
- [ ] **Frontend:** Build a `CostBreakdownSection` component that accepts `cost` and `billingCycle` props and renders the original cost, normalized monthly equivalent, and annualized yearly equivalent using a shared normalization utility (reuse or import from existing billing cycle normalization logic used by the dashboard)
- [ ] **Frontend:** Build a `StatusHistoryTimeline` component that accepts the `statusHistory` array and renders chronological entries with from/to status labels and formatted dates — including the empty/single-entry state with "No status changes recorded yet" or "Initial status" messaging
- [ ] **Frontend:** Add "Back to Subscriptions" navigation link and "Edit" button to the `SubscriptionDetailPage` with correct routing targets
- [ ] **Tests:** Write integration tests for `GET /api/subscriptions/:id` covering: valid ID returns full data, non-existent ID returns 404, statusHistory array is correctly populated and sorted
- [ ] **Tests:** Write E2E tests covering: detail page loads all metadata, cost breakdown displays correct normalized values, status history renders entries in order, 404 error state is shown for invalid ID, navigation controls work correctly

## Test Cases

### TC-1: Subscription detail page loads with complete metadata
- **Type:** E2E
- **Setup:** A subscription exists in the database with name "Netflix", category "Streaming", cost 15.99, billing cycle "monthly", start date "2024-01-01", status "Active"
- **Steps:**
  1. Navigate to the subscription list page
  2. Click on the "Netflix" subscription entry
  3. Observe the detail page
- **Expected Result:** The detail page renders and displays: name "Netflix", category "Streaming", cost "€15.99", billing cycle "Monthly", start date "1 January 2024", status "Active" — all visible and correctly labelled, with no missing fields

### TC-2: Cost breakdown displays monthly and yearly equivalent costs
- **Type:** Unit + E2E
- **Setup:** Two subscriptions: (A) cost €15.99 / monthly, (B) cost €120.00 / yearly
- **Steps (Unit):**
  1. Call the normalization utility with `{ cost: 120.00, billingCycle: 'yearly' }`
  2. Assert monthly equivalent equals `10.00`
  3. Call with `{ cost: 15.99, billingCycle: 'monthly' }`
  4. Assert yearly equivalent equals `191.88`
- **Steps (E2E):**
  1. Navigate to detail page for subscription A (€15.99/month)
  2. Verify displayed values: "€15.99 / month", "€15.99 / month", "€191.88 / year"
  3. Navigate to detail page for subscription B (€120.00/year)
  4. Verify displayed values: "€120.00 / year", "€10.00 / month", "€120.00 / year"
- **Expected Result:** All normalized cost values are correct to 2 decimal places for both billing cycles

### TC-3: Status-specific dates are displayed based on current status
- **Type:** E2E
- **Setup:** Three subscriptions: (A) status "Free Trial" with trialEndDate "2025-08-01", (B) status "Cancelled" with cancellationDate "2025-07-15" and lastActiveDate "2025-07-14", (C) status "Active" with no trial or cancellation dates
- **Steps:**
  1. Navigate to detail page for subscription A
  2. Verify "Free Trial" status label and trial end date "1 August 2025" are shown; no cancellation date visible
  3. Navigate to detail page for subscription B
  4. Verify "Cancelled" status label, cancellation date "15 July 2025", and last active date "14 July 2025" are shown
  5. Navigate to detail page for subscription C
  6. Verify "Active" status label is shown and no trial or cancellation dates are displayed
- **Expected Result:** Each status variant shows exactly the correct date fields — no extra or missing date information in any case

### TC-4: Status history is displayed in chronological order
- **Type:** Integration + E2E
- **Setup:** A subscription with statusHistory: `[{ fromStatus: 'Free Trial', toStatus: 'Active', changedAt: '2024-03-01T10:00:00Z' }, { fromStatus: 'Active', toStatus: 'Cancelled', changedAt: '2024-06-15T14:30:00Z' }]`
- **Steps:**
  1. Call `GET /api/subscriptions/:id` and inspect `statusHistory` in response
  2. Navigate to the detail page for the subscription
  3. Observe the status history timeline
- **Expected Result (Integration):** `statusHistory` array in API response has "Active → Cancelled" (changedAt 2024-06-15) listed before "Free Trial → Active" (changedAt 2024-03-01) — newest first
**Expected Result (E2E):** Timeline renders "Active → Cancelled" as the first/top entry and "Free Trial → Active" as the second entry, with correctly formatted dates

### TC-5: Subscription with no status history shows a meaningful empty state for history
- **Type:** E2E
- **Setup:** A newly created subscription with no status transitions recorded (statusHistory is empty or contains only the initial creation entry)
- **Steps:**
  1. Navigate to the detail page for the newly created subscription
  2. Locate the status history section
- **Expected Result:** The section displays either the message "No status changes recorded yet" or a single entry labelled "Initial status" with the subscription's creation date — the section is not blank, hidden, or broken

### TC-6: Navigating to a non-existent subscription shows an error state
- **Type:** E2E + Integration
- **Setup:** No subscription exists with ID `999999`
- **Steps:**
  1. (Integration) Call `GET /api/subscriptions/999999` directly
  2. (E2E) Navigate the browser to `/subscriptions/999999`
- **Expected Result (Integration):** API returns HTTP 404 with a JSON error body (e.g. `{ "error": "Subscription not found" }`)
**Expected Result (E2E):** Page displays the message "Subscription not found", a "Back to Subscriptions" navigation control is visible, and no blank/broken UI elements are rendered

### TC-7: User can navigate from the detail page back to the subscription list and to the edit form
- **Type:** E2E
- **Setup:** A subscription exists and the user is on its detail page
- **Steps:**
  1. Click the "Back" / "All Subscriptions" button or link
  2. Verify the subscription list page loads
  3. Navigate back to the detail page
  4. Click the "Edit" button
  5. Verify the subscription edit form loads with the subscription's data pre-filled
- **Expected Result:** Both navigation controls route the user to the correct destinations without errors; the edit form is pre-populated with the subscription's current data

## Technical Notes
- **API endpoints involved:**
  - `GET /api/subscriptions/:id` — primary endpoint; must return full subscription record plus `statusHistory[]`
  - Status history records must be persisted as part of the subscription update flow (story #4: Manage subscription status) — coordinate with that story's implementation to ensure history is written on every status change
- **Cost normalization:** Reuse the shared normalization utility (monthly equivalent = yearly ÷ 12, yearly equivalent = monthly × 12) already used in the dashboard aggregate calculations — do not implement a second copy; export it from a shared `utils/billing.ts` module. Use `Math.round(value * 100) / 100` or equivalent to ensure 2 decimal place precision without floating point drift
- **State management:** Fetch subscription detail data via a dedicated hook (e.g. `useSubscriptionDetail(id)`) that manages loading, error, and data states locally; no need to push single-subscription detail into global state unless the edit flow requires it
- **Routing:** Detail page route should be `/subscriptions/:id`; use the router's typed params to extract `id` and validate it is a non-empty string before dispatching the API call
- **Security:** Ensure the backend validates that the authenticated user owns the subscription before returning data (if auth is in scope for the MVP); return 404 (not 403) for unauthorized access to avoid enumeration of valid IDs
- **Performance:** The detail page fetches a single record — no pagination or aggregation needed; status history length is expected to be small (< 20 entries) so no virtualization required

## Story Points
**Estimate:** 5 points
**Reasoning:** The story spans a new backend endpoint with a relational status history model, a moderately complex frontend page with multiple distinct sections (metadata, cost breakdown, status timeline), shared utility reuse, and a comprehensive set of test cases including E2E flows — fitting comfortably within a 3–5 day scope.

## Definition of Done
- [ ] All Acceptance Criteria verified manually against a test subscription with each status type (Active, Free Trial, Cancelled) and multiple status history entries
- [ ] All Test Cases (TC-1 through TC-7) automated and passing in CI
- [ ] Code reviewed and approved by at least one other developer
- [ ] No console errors or TypeScript errors in development or production builds
- [ ] Cost normalization utility is shared with the dashboard calculation (no duplicated logic) and covered by dedicated unit tests
- [ ] `GET /api/subscriptions/:id` returns a 404 with a structured error body for non-existent or unauthorized subscription IDs