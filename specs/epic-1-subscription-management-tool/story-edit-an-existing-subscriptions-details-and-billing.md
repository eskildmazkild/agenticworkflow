<!-- GitHub Issue: #4 -->
<!-- Part of Epic: #1 -->

# Edit an existing subscription's details and billing information

## User Story
As Alex (or Jordan), I want to edit the details and billing information of an existing subscription, so that I can keep my subscription data accurate when prices change, billing cycles switch, or I need to correct a mistake.

## Background
Subscription details change over time — a streaming service may increase its monthly price, a user may switch from a monthly to an annual plan, or a subscription name may have been entered incorrectly. Without the ability to edit existing records, users are forced to delete and recreate subscriptions, losing context and continuity. This story ensures the tool always reflects the current, accurate state of each subscription.

## Acceptance Criteria

### AC-1: Open edit form pre-populated with existing data
**Given** a user is viewing the subscription list or a subscription detail page  
**When** the user clicks the "Edit" action for a specific subscription  
**Then** an edit form opens with all existing fields pre-populated with the subscription's current values (name, category, cost, billing cycle, status, start date, and any status-related dates)

---

### AC-2: Successfully save valid edits
**Given** the edit form is open with a subscription's existing data  
**When** the user modifies one or more fields with valid values and submits the form  
**Then** the subscription record is updated via a `PUT /api/subscriptions/:id` request, the form closes, and the subscription list and dashboard totals immediately reflect the updated data (including recalculated monthly/yearly cost equivalents if billing information changed)

---

### AC-3: Validation prevents saving invalid data
**Given** the edit form is open  
**When** the user clears a required field (name, cost, billing cycle, category, or start date) or enters an invalid value (e.g. negative cost, non-numeric cost, a date in an invalid format)  
**Then** the form does not submit, inline validation error messages are displayed next to the offending fields, and the user remains on the edit form

---

### AC-4: Billing cycle change recalculates normalized monthly cost
**Given** the edit form is open for a subscription with a yearly billing cycle and an annual cost of €120  
**When** the user changes the billing cycle to monthly and enters a cost of €12, then saves  
**Then** the subscription's stored cost and cycle are updated, and the dashboard reflects the corrected monthly equivalent (€12/month, not €10/month derived from the old yearly price)

---

### AC-5: Cancelling the edit discards all changes
**Given** the user has opened the edit form and modified one or more fields  
**When** the user clicks "Cancel" or closes the form without submitting  
**Then** no changes are persisted to the backend, the subscription retains its original values, and the user is returned to their previous view without any error or confirmation prompt

---

### AC-6: Edit fails gracefully on backend error
**Given** the edit form is open and the user submits valid changes  
**When** the `PUT /api/subscriptions/:id` request returns a 4xx or 5xx error  
**Then** the form remains open with the user's unsaved changes intact, a non-blocking error message is displayed (e.g. "Failed to save changes. Please try again."), and no partial update is applied to the local state

---

### AC-7: Editing a subscription does not alter its status-related dates unless explicitly changed
**Given** a subscription has a status of "Cancelled" with a cancellation date and last active date set  
**When** the user edits only the subscription's name and cost and saves  
**Then** the cancellation date and last active date remain unchanged, and the subscription status remains "Cancelled"

---

## Tasks

- [ ] **Backend:** Implement `PUT /api/subscriptions/:id` endpoint that accepts a full or partial subscription payload, validates all fields (including cross-field date logic — e.g. cancellation date must not precede start date), and returns the updated subscription object
- [ ] **Backend:** Add server-side validation rules: required fields, cost must be a positive number with up to 2 decimal places, billing cycle must be one of `[monthly, yearly]`, status must be one of `[active, trial, cancelled]`, and date constraints consistent with the status state machine
- [ ] **Frontend:** Create a reusable `SubscriptionForm` component (shared with the Create story) with controlled inputs for all subscription fields, supporting both "create" and "edit" modes — edit mode accepts an initial values prop to pre-populate all fields
- [ ] **Frontend:** Wire the edit form to the `PUT /api/subscriptions/:id` endpoint using the appropriate API client method; on success, update the subscription in global/local state and close the form; on error, surface the error message inline without discarding form state
- [ ] **Frontend:** Trigger real-time recalculation of the monthly cost equivalent in the form preview whenever the cost or billing cycle field changes, so the user can see the normalized value before saving
- [ ] **Tests:** Write integration tests for the `PUT /api/subscriptions/:id` endpoint covering: successful update, missing required fields, invalid cost value, date constraint violations, and non-existent subscription ID (404)
- [ ] **Tests:** Write E2E tests covering: opening the edit form with pre-populated data, saving a valid edit, cancelling without saving, and receiving a backend error

---

## Test Cases

### TC-1: Open edit form pre-populated with existing data
- **Type:** E2E
- **Setup:** A subscription exists in the system with name "Netflix", category "Streaming", cost €15.99, billing cycle "monthly", status "Active", start date "2023-01-01"
- **Steps:**
  1. Navigate to the subscription list
  2. Click the "Edit" button on the "Netflix" subscription
- **Expected Result:** The edit form opens with all fields pre-populated — name field shows "Netflix", category shows "Streaming", cost shows "15.99", billing cycle shows "monthly", status shows "Active", and start date shows "2023-01-01"

---

### TC-2: Successfully save valid edits
- **Type:** E2E
- **Setup:** The same "Netflix" subscription as TC-1 exists; user is on the subscription list page
- **Steps:**
  1. Click "Edit" on the "Netflix" subscription
  2. Change the cost field from "15.99" to "17.99"
  3. Click "Save"
- **Expected Result:** The form closes, the subscription list shows "Netflix" with a cost of €17.99, and the dashboard monthly total is updated to reflect the new cost. A `PUT /api/subscriptions/:id` request was made with `cost: 17.99`

---

### TC-3: Validation prevents saving invalid data
- **Type:** Integration (component-level) + E2E
- **Setup:** Edit form open for any existing subscription
- **Steps:**
  1. Clear the "Name" field
  2. Enter "-5" in the cost field
  3. Click "Save"
- **Expected Result:** Form does not submit. An error message "Name is required" appears below the name field. An error message "Cost must be a positive number" appears below the cost field. The form remains open.

---

### TC-4: Billing cycle change recalculates normalized monthly cost
- **Type:** Integration (component-level)
- **Setup:** Edit form open for a subscription with billing cycle "yearly" and cost "120"
- **Steps:**
  1. Change billing cycle to "monthly"
  2. Change cost to "12"
  3. Observe the monthly cost preview
  4. Click "Save"
- **Expected Result:** The monthly cost preview updates to "€12.00/month" (not €10.00). After save, the subscription in state reflects `cost: 12`, `billingCycle: monthly`, and the dashboard recalculates using €12/month

---

### TC-5: Cancelling the edit discards all changes
- **Type:** E2E
- **Setup:** "Netflix" subscription exists with cost €15.99
- **Steps:**
  1. Open the edit form for "Netflix"
  2. Change the cost to "99.99"
  3. Click "Cancel"
- **Expected Result:** No API call is made. The subscription list still shows "Netflix" at €15.99. The form is closed.

---

### TC-6: Edit fails gracefully on backend error
- **Type:** Integration (with mocked API)
- **Setup:** Edit form open for an existing subscription; API is mocked to return a 500 error on `PUT /api/subscriptions/:id`
- **Steps:**
  1. Change the subscription name to "Updated Name"
  2. Click "Save"
- **Expected Result:** The form remains open with "Updated Name" still entered in the name field. An error message "Failed to save changes. Please try again." is displayed. The subscription in the list retains its original name.

---

### TC-7: Editing a subscription does not alter unrelated status dates
- **Type:** Integration (API-level)
- **Setup:** A "Cancelled" subscription exists with `cancellationDate: "2024-06-01"` and `lastActiveDate: "2024-05-31"`
- **Steps:**
  1. Send a `PUT /api/subscriptions/:id` request with only `name` and `cost` fields changed
- **Expected Result:** The API response contains the updated `name` and `cost`, and `cancellationDate` remains `"2024-06-01"`, `lastActiveDate` remains `"2024-05-31"`, and `status` remains `"cancelled"`

---

## Technical Notes
- **API endpoint:** `PUT /api/subscriptions/:id` — full resource replacement preferred over `PATCH` for simplicity in MVP; if partial updates are needed later, migrate to `PATCH`
- **State management:** On successful save, the updated subscription object returned from the API must replace the existing entry in the frontend subscription list state to avoid stale data; dashboard totals must be derived values that recompute from this updated list
- **Form component reuse:** The `SubscriptionForm` component should be designed to accept an optional `initialValues` prop — when provided, the form operates in edit mode; when absent, it operates in create mode. This prevents duplicating form logic across stories 2 and 3.
- **Billing cycle normalization:** Monthly equivalent must be computed as: `monthly → cost as-is`, `yearly → cost / 12`. Use a shared utility function (e.g. `normalizeToMonthly(cost, cycle)`) to guarantee consistency between the dashboard and form preview. Use `Math.round(value * 100) / 100` to avoid floating-point drift.
- **Security:** The backend must verify that the subscription ID belongs to the authenticated user (if auth is in scope) before allowing an update, to prevent IDOR (Insecure Direct Object Reference) vulnerabilities
- **Optimistic updates:** Avoid optimistic UI updates for edits in MVP — wait for API confirmation before updating local state, given the risk of partial update confusion

---

## Story Points
**Estimate:** 5 points  
**Reasoning:** The form component logic is moderately complex (pre-population, validation, billing normalization, dual create/edit mode), the backend endpoint requires thorough validation including cross-field date rules, and the breadth of test coverage across unit, integration, and E2E layers adds meaningful effort.

---

## Definition of Done
- [ ] All Acceptance Criteria verified manually by the PO against a deployed build
- [ ] All Test Cases (TC-1 through TC-7) automated and passing in CI
- [ ] Code reviewed and approved by at least one other developer
- [ ] No console errors or TypeScript errors in development or production build
- [ ] `SubscriptionForm` component is confirmed reusable for the Create story (Story 2) with no logic duplication
- [ ] Dashboard cost totals are verified to update correctly after an edit that changes cost or billing cycle, using the shared `normalizeToMonthly` utility