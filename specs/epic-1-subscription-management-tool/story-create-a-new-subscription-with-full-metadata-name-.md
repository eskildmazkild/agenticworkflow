<!-- GitHub Issue: #3 -->
<!-- Part of Epic: #1 -->

# Create a new subscription with full metadata (name, category, cost, billing cycle, start date, status)

## User Story
As Alex (an individual managing personal subscriptions), I want to add a new subscription with all relevant details — including name, category, cost, billing cycle, start date, and status — so that I have a complete and accurate record of the service from day one and it is immediately reflected in my cost totals and dashboard overview.

## Background
Users currently track subscriptions manually in spreadsheets or not at all, leading to forgotten services and financial waste. This story is the primary data-entry point for the entire tool — without the ability to create subscriptions with full metadata, no other feature (dashboard totals, filtering, status tracking) has data to operate on. Getting the data model and validation right here is critical, as downstream features depend on the integrity of records created through this form.

---

## Acceptance Criteria

### AC-1: Successfully create a subscription with all required fields
**Given** the user is on the subscription list or dashboard page  
**When** the user opens the "Add Subscription" form, fills in all required fields (name, category, cost, billing cycle, start date, status), and submits  
**Then** the new subscription is persisted via the API, appears immediately in the subscription list with correct metadata, and the dashboard cost totals are updated to reflect the new subscription's normalized monthly cost

### AC-2: Form validation prevents submission with missing required fields
**Given** the user has opened the "Add Subscription" form  
**When** the user attempts to submit the form while one or more required fields (name, category, cost, billing cycle, start date, status) are empty or invalid  
**Then** the form is not submitted, each invalid field displays a specific inline error message, and focus is moved to the first invalid field

### AC-3: Cost field accepts only valid positive numeric values
**Given** the user is filling in the cost field  
**When** the user enters a non-numeric value, zero, or a negative number  
**Then** an inline validation error is shown (e.g. "Cost must be a number greater than 0") and the form cannot be submitted until corrected; values with more than 2 decimal places are either rejected or automatically rounded to 2 decimal places

### AC-4: Selecting "Free Trial" status requires a trial end date
**Given** the user has selected "Free Trial" as the subscription status  
**When** the user submits the form without providing a trial end date  
**Then** an inline validation error is shown on the trial end date field (e.g. "Trial end date is required for Free Trial status") and submission is blocked; the trial end date field must also be on or after the start date

### AC-5: Selecting "Cancelled" status requires a cancellation date
**Given** the user has selected "Cancelled" as the subscription status  
**When** the user submits the form without providing a cancellation date  
**Then** an inline validation error is shown (e.g. "Cancellation date is required for Cancelled status") and submission is blocked; the cancellation date must be on or after the start date

### AC-6: Conditional date fields appear and disappear based on selected status
**Given** the user is interacting with the status dropdown  
**When** the user selects "Free Trial"  
**Then** a "Trial end date" date picker appears in the form; **when** the user then changes the status to "Active"  **then** the trial end date field is hidden and any previously entered value is cleared; **when** the user selects "Cancelled" **then** a "Cancellation date" field appears instead

### AC-7: Yearly billing cycle displays the normalized monthly equivalent cost
**Given** the user has entered a cost and selected "Yearly" as the billing cycle  
**When** the cost field or billing cycle field loses focus (or in real time)  
**Then** the form displays a helper text showing the normalized monthly equivalent (e.g. "≈ €X.XX / month") calculated as `yearly cost / 12`, rounded to 2 decimal places; this normalized value is what is used for dashboard cost aggregation

---

## Tasks

- [ ] **Backend:** Define and implement the `Subscription` data model/schema with fields: `id`, `name`, `category` (enum), `cost` (decimal), `billingCycle` (enum: `monthly` | `yearly`), `normalizedMonthlyCost` (decimal, computed), `startDate`, `status` (enum: `active` | `free_trial` | `cancelled`), `trialEndDate` (nullable), `cancellationDate` (nullable), `createdAt`, `updatedAt`
- [ ] **Backend:** Implement `POST /api/subscriptions` endpoint that validates the request body (required fields, type checks, conditional date rules), computes `normalizedMonthlyCost`, persists the record, and returns the created subscription with HTTP 201; return HTTP 422 with structured field-level errors on validation failure
- [ ] **Backend:** Write server-side validation rules enforcing: cost > 0, `trialEndDate` required and ≥ `startDate` when status is `free_trial`, `cancellationDate` required and ≥ `startDate` when status is `cancelled`, category and status values are valid enum members
- [ ] **Frontend:** Build the `AddSubscriptionForm` component with controlled inputs for all fields, a status-driven conditional rendering strategy for `trialEndDate` and `cancellationDate` fields, and real-time monthly cost normalization display for yearly billing cycle
- [ ] **Frontend:** Implement client-side form validation using a schema validation library (e.g. Zod + React Hook Form) mirroring all backend validation rules, with inline per-field error messages and focus management on submit failure; trigger validation on blur per field and on submit
- [ ] **Frontend:** Wire the form submission to `POST /api/subscriptions`, handle the success response by updating the global subscription list state and closing/resetting the form, and handle API error responses (422) by mapping field-level errors back to the corresponding form fields
- [ ] **Tests:** Write integration tests for `POST /api/subscriptions` covering: successful creation (monthly and yearly), missing required fields, invalid cost values, missing conditional dates (trial/cancelled), and date ordering violations
- [ ] **Tests:** Write E2E tests covering the happy path (create active monthly subscription, verify it appears in list and dashboard total updates) and key error paths (submit empty form, select Free Trial without trial end date)

---

## Test Cases

### TC-1: Successfully create a subscription with all required fields
- **Type:** E2E
- **Setup:** Application is running; subscription list is empty or has existing entries; user is on the dashboard or subscription list page
- **Steps:**
  1. Click the "Add Subscription" button
  2. Enter name: "Netflix"
  3. Select category: "Streaming"
  4. Enter cost: "15.99"
  5. Select billing cycle: "Monthly"
  6. Enter start date: "2024-01-01"
  7. Select status: "Active"
  8. Click "Save" / "Add Subscription"
- **Expected Result:** The modal/form closes, "Netflix" appears in the subscription list with cost €15.99/month, category "Streaming", status "Active", and the dashboard monthly total increases by €15.99

### TC-2: Form validation prevents submission with missing required fields
- **Type:** E2E
- **Setup:** "Add Subscription" form is open with all fields empty
- **Steps:**
  1. Click "Save" without filling in any fields
- **Expected Result:** Form is not submitted (no API call made); inline error messages appear beneath each required field (name, category, cost, billing cycle, start date, status); focus moves to the first invalid field (name)

### TC-3: Cost field accepts only valid positive numeric values
- **Type:** Integration (component-level)
- **Setup:** `AddSubscriptionForm` is rendered in isolation
- **Steps:**
  1. Enter "-5" in the cost field, tab away → expect error "Cost must be a number greater than 0"
  2. Clear and enter "0", tab away → expect same error
  3. Clear and enter "abc", tab away → expect same error
  4. Clear and enter "9.999", tab away → expect value to be rounded to "10.00" or an error shown
  5. Clear and enter "9.99", tab away → expect no error
- **Expected Result:** Errors shown for steps 1–3; step 4 results in either rounding or a validation error; step 5 passes with no error

### TC-4: Selecting "Free Trial" status requires a trial end date
- **Type:** Integration (API) + E2E
- **Setup (API):** POST body with status `free_trial` and no `trialEndDate`
- **Steps (API):**
  1. Send `POST /api/subscriptions` with `{ name: "Spotify", category: "streaming", cost: 9.99, billingCycle: "monthly", startDate: "2024-03-01", status: "free_trial" }` (no `trialEndDate`)
- **Expected Result (API):** HTTP 422 response with error referencing `trialEndDate` field
- **Steps (E2E):**
  1. Open form, select status "Free Trial", fill all other fields, leave trial end date empty, click Save
- **Expected Result (E2E):** Form not submitted; inline error on trial end date field: "Trial end date is required for Free Trial status"

### TC-5: Selecting "Cancelled" status requires a cancellation date
- **Type:** Integration (API) + E2E
- **Setup (API):** POST body with status `cancelled` and no `cancellationDate`
- **Steps (API):**
  1. Send `POST /api/subscriptions` with `{ name: "Hulu", category: "streaming", cost: 7.99, billingCycle: "monthly", startDate: "2024-01-01", status: "cancelled" }` (no `cancellationDate`)
- **Expected Result (API):** HTTP 422 with error referencing `cancellationDate`
- **Steps (E2E):**
  1. Open form, select status "Cancelled", fill all other fields, leave cancellation date empty, click Save
- **Expected Result (E2E):** Form not submitted; inline error: "Cancellation date is required for Cancelled status"

### TC-6: Conditional date fields appear and disappear based on selected status
- **Type:** Integration (component-level)
- **Setup:** `AddSubscriptionForm` rendered; status defaults to "Active"
- **Steps:**
  1. Confirm neither "Trial end date" nor "Cancellation date" fields are visible
  2. Change status to "Free Trial" → confirm "Trial end date" field appears; "Cancellation date" is not visible
  3. Enter a date in "Trial end date"
  4. Change status to "Active" → confirm "Trial end date" field disappears and its value is cleared
  5. Change status to "Cancelled" → confirm "Cancellation date" field appears; "Trial end date" is not visible
- **Expected Result:** Conditional fields render only for their respective statuses; previously entered values are cleared when status changes away

### TC-7: Yearly billing cycle displays the normalized monthly equivalent cost
- **Type:** Integration (component-level) + Integration (API)
- **Setup (component):** `AddSubscriptionForm` rendered
- **Steps (component):**
  1. Enter cost: "120.00"
  2. Select billing cycle: "Yearly"
  3. Observe helper text near cost field
- **Expected Result (component):** Helper text displays "≈ €10.00 / month"
- **Setup (API):** Full valid POST body with `cost: 120.00` and `billingCycle: "yearly"`
- **Steps (API):**
  1. Send `POST /api/subscriptions` with yearly cost of 120.00
- **Expected Result (API):** Response body contains `normalizedMonthlyCost: 10.00`; this value is used in dashboard aggregation

---

## Technical Notes

- **API endpoints:** `POST /api/subscriptions` — returns the full created subscription object on 201; on 422 returns `{ errors: { fieldName: "error message", ... } }` for field-level mapping in the frontend
- **Normalized cost computation:** `normalizedMonthlyCost = billingCycle === 'yearly' ? cost / 12 : cost` — computed server-side and stored; frontend displays it as a hint but does not send it in the request body to avoid client/server drift
- **State management:** On successful creation, the new subscription must be appended to the global subscriptions list (e.g. React Query cache invalidation or optimistic update) so that the dashboard cost totals re-compute without a full page reload
- **Status state machine:** At creation time, all three statuses (Active, Free Trial, Cancelled) are valid entry points — the state machine constraints (e.g. transition rules) are enforced more strictly in the Edit story; however, the conditional date validation rules defined here must be consistent with the state machine defined for that story
- **Date inputs:** Use ISO 8601 format (`YYYY-MM-DD`) for all date values in API payloads; the frontend date pickers must serialize to this format before submission
- **Decimal precision:** Store cost and normalizedMonthlyCost as `DECIMAL(10, 2)` in the database; avoid floating-point arithmetic — use a decimal library (e.g. `decimal.js`) if JavaScript-side calculations are needed
- **Security:** Sanitize and validate all string inputs server-side to prevent injection; ensure `category` and `status` values are validated against their enum lists server-side regardless of frontend constraints

---

## Story Points
**Estimate:** 5 points  
**Reasoning:** The form itself is moderately complex due to conditional field logic, client- and server-side validation mirroring, billing cycle normalization display, and the need to keep dashboard state in sync — but it is a well-scoped, single-concern story with no external integrations.

---

## Definition of Done
- [ ] All Acceptance Criteria verified manually by the PO against the running application
- [ ] All Test Cases (TC-1 through TC-7) automated and passing in CI
- [ ] Code reviewed and approved by at least one other developer
- [ ] No console errors or TypeScript errors (`tsc --noEmit` passes cleanly)
- [ ] Server-side validation is fully independent of client-side validation (API returns correct 422 errors even when called directly without the UI)
- [ ] Normalized monthly cost is correctly stored in the database and reflected in dashboard totals immediately after creation, verified with at least one automated E2E assertion on the dashboard total