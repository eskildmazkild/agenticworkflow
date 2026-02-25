<!-- GitHub Issue: #7 -->
<!-- Part of Epic: #1 -->

# Filter and sort the subscription list by status, category, and cost

## User Story
As Alex (or Jordan), I want to filter the subscription list by status and category, and sort it by cost, name, or status, so that I can quickly locate specific subscriptions and understand which services are driving my highest spending.

## Background
Users with many subscriptions need more than a flat list — they need to slice and rank that list to answer questions like "what active subscriptions am I paying the most for?" or "which streaming services have I cancelled?". Without filtering and sorting, the list becomes harder to parse as it grows, and spending patterns remain hidden. This story delivers the controls that make the subscription list genuinely useful for decision-making.

## Acceptance Criteria

### AC-1: Filter by status
**Given** the subscription list contains subscriptions with statuses Active, Free Trial, and Cancelled
**When** the user selects one or more status values from the status filter (e.g. "Active")
**Then** only subscriptions matching the selected status(es) are shown in the list, and the count of visible subscriptions updates to reflect the filtered result

### AC-2: Filter by category
**Given** the subscription list contains subscriptions across multiple categories (e.g. Streaming, Software, Fitness)
**When** the user selects one or more categories from the category filter
**Then** only subscriptions belonging to the selected category(ies) are shown, and the count of visible subscriptions updates accordingly

### AC-3: Combine status and category filters simultaneously
**Given** the user has selected a status filter (e.g. "Active") and a category filter (e.g. "Streaming")
**When** both filters are active at the same time
**Then** only subscriptions that match **both** criteria are displayed (AND logic), and the visible list and count reflect the intersection

### AC-4: Sort the list
**Given** the subscription list is visible (with or without filters applied)
**When** the user selects a sort option from the sort control (options: Name A→Z, Name Z→A, Monthly Cost High→Low, Monthly Cost Low→High, Start Date Newest→Oldest, Start Date Oldest→Newest)
**Then** the visible subscription list is reordered according to the selected sort option without clearing any active filters; cost sorting uses the normalized monthly equivalent value for all billing cycles

### AC-5: Empty state when no subscriptions match filters
**Given** the user has applied one or more filters
**When** no subscriptions match the active filter combination
**Then** an empty state message is displayed (e.g. "No subscriptions match your current filters.") with a "Clear filters" action, and no list items or cost totals from the main list are shown in the filtered area

### AC-6: Reset all filters and sort
**Given** the user has one or more active filters or a non-default sort applied
**When** the user clicks the "Clear filters" button or resets the sort to its default
**Then** all filter selections are cleared, the sort reverts to default (Name A→Z), and the full unfiltered subscription list is restored

### AC-7: Filter and sort state persists within the session
**Given** the user has applied filters and/or a sort order and navigates away to a subscription detail page
**When** the user returns to the subscription list
**Then** the previously selected filters and sort order are still applied and the list reflects those selections

## Tasks

- [ ] **Backend:** Extend the `GET /api/subscriptions` endpoint to accept query parameters: `status` (multi-value), `category` (multi-value), `sortBy` (`name | monthlyCost | startDate`), and `sortOrder` (`asc | desc`) — apply filtering and sorting server-side and return filtered results with a `total` count field in the response body
- [ ] **Backend:** Ensure cost sorting uses the normalized monthly equivalent value (yearly cost ÷ 12) consistently in the sort logic, with tie-breaking by name ascending
- [ ] **Frontend:** Build a `SubscriptionFilters` component containing: a multi-select status filter (chips or checkboxes for Active, Free Trial, Cancelled), a multi-select category filter (chips or checkboxes), a sort dropdown, and a "Clear filters" button — button is only enabled when at least one filter or non-default sort is active
- [ ] **Frontend:** Connect `SubscriptionFilters` to the subscription list data layer — on any filter/sort change, issue a new API request (or re-derive from cached data) and update the visible list and visible-count display; debounce filter changes by 200 ms to avoid excessive requests
- [ ] **Frontend:** Persist active filter and sort state in a React context or URL query string (e.g. `?status=active&category=streaming&sortBy=monthlyCost&sortOrder=desc`) so state survives in-session navigation
- [ ] **Frontend:** Implement the empty state UI for the subscription list when the filtered result set is empty, including the "Clear filters" shortcut action
- [ ] **Tests:** Write integration tests for the `GET /api/subscriptions` endpoint covering single-filter, multi-filter (AND logic), combined status+category filter, each sort option, and the empty-result case
- [ ] **Tests:** Write E2E tests covering: applying a status filter, combining status+category filters, sorting by cost, verifying empty state, and clearing all filters

## Test Cases

### TC-1: Filter by status
- **Type:** E2E
- **Setup:** Seed database with 3 Active, 2 Free Trial, and 2 Cancelled subscriptions
- **Steps:**
  1. Navigate to the subscription list page
  2. Select "Active" from the status filter
- **Expected Result:** Exactly 3 subscriptions are displayed; the visible-count indicator shows "3"; no Free Trial or Cancelled subscriptions appear

### TC-2: Filter by category
- **Type:** E2E
- **Setup:** Seed database with 2 Streaming, 3 Software, and 1 Fitness subscription
- **Steps:**
  1. Navigate to the subscription list page
  2. Select "Streaming" from the category filter
- **Expected Result:** Exactly 2 subscriptions are displayed; no Software or Fitness subscriptions appear; count shows "2"

### TC-3: Combine status and category filters simultaneously
- **Type:** Integration
- **Setup:** Seed API with: 2 Active Streaming, 1 Cancelled Streaming, 2 Active Software subscriptions
- **Steps:**
  1. Call `GET /api/subscriptions?status=active&category=streaming`
- **Expected Result:** Response contains exactly 2 records; all records have `status: "active"` and `category: "streaming"`; `total` field equals 2

### TC-4: Sort the list
- **Type:** Integration
- **Setup:** Seed API with subscriptions having normalized monthly costs: £5.00 (yearly £60), £12.99, £3.49
- **Steps:**
  1. Call `GET /api/subscriptions?sortBy=monthlyCost&sortOrder=desc`
- **Expected Result:** Response array order is £12.99, £5.00 (normalized from £60/12), £3.49; yearly-billed subscription is correctly normalized before sorting

### TC-5: Empty state when no subscriptions match filters
- **Type:** E2E
- **Setup:** Seed database with only Active Streaming subscriptions (no Fitness subscriptions)
- **Steps:**
  1. Navigate to the subscription list page
  2. Select "Fitness" from the category filter
- **Expected Result:** The subscription list area shows the message "No subscriptions match your current filters."; a "Clear filters" button is visible; no subscription cards are rendered

### TC-6: Reset all filters and sort
- **Type:** E2E
- **Setup:** Seed database with mixed subscriptions; user has "Cancelled" status filter and "Cost High→Low" sort active
- **Steps:**
  1. Confirm filtered/sorted list is showing
  2. Click "Clear filters"
- **Expected Result:** Status and category filter selections are cleared; sort reverts to "Name A→Z"; the full list of all subscriptions is restored; the "Clear filters" button becomes disabled or hidden

### TC-7: Filter and sort state persists within the session
- **Type:** E2E
- **Setup:** Seed database with subscriptions of varying statuses and categories
- **Steps:**
  1. Navigate to the subscription list page
  2. Select "Active" status filter and "Cost High→Low" sort
  3. Click on any subscription to open its detail page
  4. Click the browser back button or the "Back to list" link
- **Expected Result:** On returning to the list, the "Active" status filter and "Cost High→Low" sort are still applied; the list displays the same filtered and sorted results as before navigation

## Technical Notes
- **API endpoints involved:** `GET /api/subscriptions` — extend with query params `status[]`, `category[]`, `sortBy`, `sortOrder`; the response envelope should include `{ data: Subscription[], total: number }`
- **Filtering logic:** Status and category filters use AND logic between filter types (i.e. status AND category) and OR logic within a filter type (i.e. Active OR Cancelled), matching standard multi-select UX conventions
- **Cost normalization for sorting:** The backend must sort by `monthlyCost` computed field (`cost` for monthly-billed; `cost / 12` for yearly-billed), not the raw `cost` field — this must be consistent with how the dashboard calculates totals
- **State management:** Filter/sort state should be mirrored in URL query parameters (via `useSearchParams` or equivalent) to enable shareable/bookmarkable filtered views and free in-session persistence without a separate store; on mount, initialize state from URL params
- **Performance:** For typical personal-use list sizes (< 200 subscriptions) server-side filtering is acceptable; if data is cached client-side, filtering and sorting should be derived computations (e.g. `useMemo`) to avoid redundant re-renders
- **Default sort:** The default sort order is Name A→Z; this should be the fallback when no `sortBy` parameter is provided

## Story Points
**Estimate:** 5 points
**Reasoning:** The filtering and sorting logic itself is straightforward, but the combination of multi-value filter params, URL state persistence, backend query extension, normalized cost sorting, and full E2E coverage across all permutations pushes this beyond a simple 3-point story.

## Definition of Done
- [ ] All Acceptance Criteria verified manually
- [ ] All Test Cases automated and passing
- [ ] Code reviewed and approved
- [ ] No console errors or TypeScript errors
- [ ] Filter and sort parameters are reflected in the URL and correctly restore list state on page reload within the same session
- [ ] Cost sorting confirmed to use normalized monthly equivalent values for both monthly and yearly-billed subscriptions, verified with a mixed billing cycle dataset