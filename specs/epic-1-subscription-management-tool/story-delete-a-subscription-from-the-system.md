<!-- GitHub Issue: #6 -->
<!-- Part of Epic: #1 -->

# Delete a subscription from the system

## User Story
As Alex, a user managing personal subscriptions, I want to permanently delete a subscription from the system, so that my dashboard and cost totals accurately reflect only the services I am currently tracking and I am not cluttered by irrelevant entries.

## Background
Users will inevitably need to remove subscriptions that were added by mistake, are duplicates, or are no longer relevant to track even as cancelled entries. Without a delete capability, the subscription list becomes polluted over time, degrading the usefulness of the dashboard and cost summaries. This story ensures users have full control over their data.

## Acceptance Criteria

### AC-1: Delete a subscription via confirmation dialog
**Given** the user is on the subscription list or the detail view of a subscription
**When** the user clicks the "Delete" action for a specific subscription
**Then** a confirmation dialog is displayed asking the user to confirm the permanent deletion, showing the subscription name so the user can verify they are deleting the correct item

### AC-2: Confirmed deletion removes the subscription and updates the dashboard
**Given** the confirmation dialog is open for a specific subscription
**When** the user confirms the deletion
**Then** the subscription is permanently removed from the backend, disappears from the subscription list, and all dashboard cost totals (monthly, yearly, and per-category) are recalculated and updated to reflect the removal

### AC-3: Cancelling the deletion dialog leaves data unchanged
**Given** the confirmation dialog is open for a specific subscription
**When** the user clicks "Cancel" or dismisses the dialog (e.g., presses Escape or clicks outside the dialog)
**Then** the dialog closes, the subscription remains in the system, and no data is changed

### AC-4: Deletion of a non-existent or already-deleted subscription is handled gracefully
**Given** a subscription has already been deleted (e.g., in another browser tab) or the record no longer exists in the backend
**When** the user confirms the deletion of that subscription
**Then** the API returns a `404 Not Found` response, the UI displays a user-friendly error message (e.g., "This subscription could not be found. It may have already been deleted."), and the local subscription list is refreshed to reflect the current server state

### AC-5: Network or server error during deletion is handled gracefully
**Given** the confirmation dialog is open and the user confirms the deletion
**When** the API call fails due to a network error or a `5xx` server error
**Then** the dialog closes or remains open with an inline error message (e.g., "Something went wrong. Please try again."), the subscription is NOT removed from the list, and the user can retry the action

### AC-6: Deletion is visually indicated during the API call
**Given** the user has confirmed the deletion
**When** the API call is in-flight
**Then** the confirmation button shows a loading/spinner state and is disabled to prevent duplicate requests, and the cancel button is also disabled during the pending state

### AC-7: Deleted subscription is excluded from all aggregated cost calculations
**Given** a subscription with a known cost (e.g., €9.99/month, category: Streaming) exists and contributes to dashboard totals
**When** the subscription is successfully deleted
**Then** the monthly total, yearly total, and the Streaming category total on the dashboard are each reduced by the correct normalized amount corresponding to the deleted subscription's cost and billing cycle

## Tasks

- [ ] **Backend:** Implement `DELETE /api/subscriptions/:id` endpoint that permanently removes the subscription record; return `204 No Content` on success, `404 Not Found` if the record does not exist, and `500` on server error *(include authorization check to ensure the subscription belongs to the requesting user)*
- [ ] **Frontend:** Add a "Delete" action button/icon to each subscription row in the subscription list and to the subscription detail view
- [ ] **Frontend:** Build a reusable `ConfirmationDialog` component that accepts a title, body message (including the subscription name), a confirm callback, a cancel callback, and a loading state prop
- [ ] **Frontend:** Implement the delete flow: on confirm, call `DELETE /api/subscriptions/:id`, handle loading/success/error states, remove the item from local state on success, and display inline error messages on failure
- [ ] **Frontend:** Ensure dashboard cost aggregation (monthly, yearly, per-category totals) reactively recalculates when the subscription list state changes after a successful deletion
- [ ] **Tests:** Write integration tests for the `DELETE /api/subscriptions/:id` endpoint covering: successful deletion (204), deletion of non-existent resource (404), and unauthorized access (401/403)
- [ ] **Tests:** Write E2E tests covering: successful delete flow, cancel/dismiss dialog flow, and error handling (mocked 500 response)

## Test Cases

### TC-1: Delete a subscription via confirmation dialog
- **Type:** E2E
- **Setup:** At least one subscription exists in the system (e.g., "Netflix", €12.99/month, Streaming); user is on the subscription list page
- **Steps:**
  1. Locate the "Netflix" subscription row
  2. Click the "Delete" button/icon for that row
  3. Observe the confirmation dialog
- **Expected Result:** A confirmation dialog is displayed containing the text "Netflix" (the subscription name) and a confirm and cancel button

### TC-2: Confirmed deletion removes the subscription and updates the dashboard
- **Type:** E2E
- **Setup:** "Netflix" subscription (€12.99/month, Streaming) exists; dashboard totals are pre-recorded; user has opened the confirmation dialog
- **Steps:**
  1. Click the "Confirm" / "Delete" button in the confirmation dialog
  2. Wait for the API response
  3. Observe the subscription list
  4. Navigate to or observe the dashboard totals
- **Expected Result:** "Netflix" no longer appears in the subscription list; monthly total is reduced by €12.99; yearly total is reduced by €155.88; Streaming category total is reduced by €12.99

### TC-3: Cancelling the deletion dialog leaves data unchanged
- **Type:** E2E
- **Setup:** "Netflix" subscription exists; confirmation dialog is open
- **Steps:**
  1. Click the "Cancel" button in the dialog
  2. Observe the subscription list and dialog state
- **Expected Result:** The dialog closes; "Netflix" still appears in the subscription list; all dashboard totals remain unchanged

### TC-4: Deletion of a non-existent subscription is handled gracefully
- **Type:** Integration / E2E
- **Setup:** Mock the `DELETE /api/subscriptions/:id` endpoint to return `404 Not Found`; confirmation dialog is open
- **Steps:**
  1. Click the "Confirm" button in the dialog
  2. Wait for the API response
  3. Observe the UI
- **Expected Result:** A user-friendly error message is shown (e.g., "This subscription could not be found. It may have already been deleted."); the subscription list is refreshed from the server; no crash or unhandled error occurs

### TC-5: Network or server error during deletion is handled gracefully
- **Type:** Integration / E2E
- **Setup:** Mock the `DELETE /api/subscriptions/:id` endpoint to return `500 Internal Server Error`; confirmation dialog is open
- **Steps:**
  1. Click the "Confirm" button in the dialog
  2. Wait for the API response
  3. Observe the subscription list and dialog/error state
- **Expected Result:** An error message is displayed (e.g., "Something went wrong. Please try again."); the subscription remains in the list; the user is able to retry

### TC-6: Deletion is visually indicated during the API call
- **Type:** E2E (with artificial network delay / mocked slow response)
- **Setup:** Mock the `DELETE` endpoint with a 2-second delay; confirmation dialog is open
- **Steps:**
  1. Click the "Confirm" button
  2. Immediately observe the dialog button states during the in-flight request
- **Expected Result:** The confirm button displays a loading indicator and is disabled; the cancel button is also disabled; no duplicate API calls are triggered by additional clicks

### TC-7: Deleted subscription is excluded from all aggregated cost calculations
- **Type:** Integration
- **Setup:** Seed the state with two subscriptions: "Netflix" (€12.99/month, Streaming) and "Spotify" (€9.99/month, Streaming); verify initial totals (monthly: €22.98, Streaming: €22.98)
- **Steps:**
  1. Delete "Netflix" via the confirmed delete flow
  2. Read the updated dashboard totals from the UI state or rendered output
- **Expected Result:** Monthly total = €9.99; yearly total = €119.88; Streaming category total = €9.99; "Spotify" remains unaffected

## Technical Notes
- **API endpoint:** `DELETE /api/subscriptions/:id` → `204 No Content` (success), `404 Not Found` (not found), `401 Unauthorized` / `403 Forbidden` (auth)
- **Authorization:** The backend must verify the subscription `:id` belongs to the authenticated user before deleting — never delete by ID alone without an ownership check
- **State management:** On successful deletion, remove the subscription from the client-side subscription list (e.g., filter by id); dashboard totals should be derived/computed values from this list so they update automatically without a separate API call
- **No soft delete:** This is a hard delete per the epic scope — there is no "archived" or "undo" state; make the confirmation dialog copy clearly communicate this is permanent
- **Optimistic update consideration:** Do NOT use optimistic deletion — given the permanent nature of this action, wait for API confirmation before updating the UI to avoid confusing the user if the request fails
- **Confirmation dialog reusability:** The `ConfirmationDialog` component will likely be reused in future stories (e.g., bulk delete, cancel subscription) — design it as a generic modal accepting props rather than a subscription-specific component

## Story Points
**Estimate:** 3 points
**Reasoning:** The core delete flow is straightforward, but the confirmation dialog component, comprehensive error handling (404, 500, network), loading states, and ensuring dashboard totals reactively update together constitute a moderate but well-scoped body of work.

## Definition of Done
- [ ] All Acceptance Criteria verified manually in Chrome, Firefox, and Safari
- [ ] All Test Cases (TC-1 through TC-7) automated and passing in CI
- [ ] Code reviewed and approved by at least one other developer
- [ ] No console errors or TypeScript errors
- [ ] Dashboard cost totals are verified to update correctly after deletion for both monthly and yearly billing cycles
- [ ] Confirmation dialog displays the subscription name to prevent accidental deletion of the wrong subscription