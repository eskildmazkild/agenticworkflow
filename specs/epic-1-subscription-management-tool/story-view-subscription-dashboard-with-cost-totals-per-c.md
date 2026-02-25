<!-- GitHub Issue: #2 -->
<!-- Part of Epic: #1 -->

# View subscription dashboard with cost totals per category, month, and year

## User Story
As Alex (an individual managing personal subscriptions), I want to see a dashboard that shows all my subscriptions grouped by category with their total monthly and yearly costs, so that I can immediately understand how much I am spending and where, without manually tracking it in a spreadsheet.

## Background
Users with many subscriptions across different services (streaming, SaaS, fitness, etc.) have no single place to see their total recurring spend. Without a centralized overview, it is easy to lose track of costs — especially for yearly-billed subscriptions that feel "invisible" month-to-month. This dashboard is the primary entry point of the tool and the highest-value screen for all personas.

## Acceptance Criteria

### AC-1: Dashboard displays all active and trial subscriptions grouped by category with per-category cost totals
**Given** the user has subscriptions in multiple categories (e.g. Streaming, Software, Fitness)
**When** the user navigates to the dashboard
**Then** each category is displayed as a distinct group, listing the subscriptions within it, and showing the sum of monthly-equivalent costs for that category

### AC-2: Dashboard displays a grand total monthly cost and a grand total yearly cost across all non-cancelled subscriptions
**Given** the user has a mix of monthly-billed and yearly-billed subscriptions with statuses Active or Free Trial
**When** the user views the dashboard
**Then** a summary section displays the total monthly cost (sum of all monthly-equivalent costs) and the total yearly cost (total monthly cost × 12), excluding all subscriptions with status Cancelled

### AC-3: Yearly-billed subscriptions are normalized to a monthly equivalent cost for all totals
**Given** a subscription is billed yearly (e.g. £120/year)
**When** the user views the dashboard
**Then** the subscription is displayed with its monthly equivalent cost (e.g. £10.00/month) used in all category and grand total calculations, while the original yearly price is also visible on the subscription entry

### AC-4: Cancelled subscriptions are visually distinct and excluded from cost totals
**Given** the user has one or more subscriptions with status Cancelled
**When** the user views the dashboard
**Then** cancelled subscriptions are shown in a visually distinct style (e.g. greyed out with a "Cancelled" badge) and are not included in any category total or grand total cost calculation

### AC-5: Free Trial subscriptions are visually distinct, included in cost totals, and display their trial end date
**Given** the user has one or more subscriptions with status Free Trial
**When** the user views the dashboard
**Then** Free Trial subscriptions are displayed with a "Free Trial" badge and their trial end date, and their cost (if non-zero) is included in the category and grand total calculations

### AC-6: Empty state is shown when the user has no subscriptions
**Given** the user has no subscriptions recorded
**When** the user navigates to the dashboard
**Then** an empty state message is displayed (e.g. "No subscriptions yet — add your first one") with a call-to-action button to create a new subscription, and all cost totals display as £0.00

### AC-7: Dashboard cost totals update in real time when subscriptions are added, edited, or deleted
**Given** the user is viewing the dashboard
**When** the user adds a new subscription, edits an existing one, or deletes one (via actions accessible from the dashboard)
**Then** all category totals and grand totals are recalculated and updated immediately without requiring a full page reload

## Tasks

- [ ] **Backend:** Create `GET /api/subscriptions` endpoint that returns all subscriptions for the user, including fields: `id`, `name`, `category`, `cost`, `billingCycle` (`monthly` | `yearly`), `status` (`active` | `trial` | `cancelled`), `trialEndDate`, `cancellationDate`, `startDate` *(response must support future filtering via query params for story 6)*
- [ ] **Backend:** Implement monthly-equivalent cost normalization logic server-side: `monthlyCost = billingCycle === 'yearly' ? cost / 12 : cost`, returned as `monthlyCostEquivalent` on each subscription record, rounded to 2 decimal places
- [ ] **Frontend:** Build `DashboardPage` component that fetches subscriptions on mount and renders the category groups, per-category totals, and grand total summary section
- [ ] **Frontend:** Build `CategoryGroup` component that accepts a category name and list of subscriptions, renders each as a `SubscriptionCard`, and displays the summed monthly-equivalent cost for that category
- [ ] **Frontend:** Build `CostSummaryBar` component displaying total monthly cost and total yearly cost (monthly × 12), derived only from non-cancelled subscriptions; format all monetary values to 2 decimal places with currency symbol
- [ ] **Frontend:** Implement visual distinction for subscription statuses in `SubscriptionCard`: Active (default style), Free Trial (badge + trial end date displayed), Cancelled (greyed-out style + "Cancelled" badge, excluded from totals)
- [ ] **Frontend:** Implement empty state UI in `DashboardPage` when the subscriptions array is empty, including a CTA button linking to the create subscription flow
- [ ] **Tests:** Write unit tests for the cost normalization and aggregation utility functions (monthly equivalent, per-category sum, grand total, excluding cancelled)

## Test Cases

### TC-1: Dashboard displays subscriptions grouped by category with per-category totals
- **Type:** E2E
- **Setup:** Seed 4 subscriptions — 2 in "Streaming" (£10/month active, £120/year active), 1 in "Fitness" (£30/month active), 1 in "Software" (£20/month active)
- **Steps:**
  1. Navigate to the dashboard URL
  2. Assert that three category groups are rendered: "Streaming", "Fitness", "Software"
  3. Assert the "Streaming" category total displays £20.00/month (£10 + £10 normalized from £120/year)
  4. Assert the "Fitness" category total displays £30.00/month
  5. Assert the "Software" category total displays £20.00/month
- **Expected Result:** All three category groups are visible with correct subscription counts and correct monthly-equivalent cost totals

### TC-2: Grand total monthly and yearly costs are correctly calculated and displayed
- **Type:** E2E
- **Setup:** Seed 3 active subscriptions: £10/month, £20/month, £120/year (= £10/month equivalent); total monthly = £40.00, total yearly = £480.00
- **Steps:**
  1. Navigate to the dashboard URL
  2. Locate the cost summary section
  3. Assert the total monthly cost displays £40.00
  4. Assert the total yearly cost displays £480.00
- **Expected Result:** Summary section shows £40.00/month and £480.00/year

### TC-3: Yearly-billed subscriptions show monthly equivalent and original yearly price
- **Type:** Integration
- **Setup:** One subscription: name "Annual Plan", cost £120, billingCycle `yearly`, status `active`
- **Steps:**
  1. Render `SubscriptionCard` with the above subscription data
  2. Assert the card displays "£10.00/month" as the normalized cost
  3. Assert the card also displays "£120.00/year" as the original billing amount
- **Expected Result:** Both the monthly equivalent (£10.00) and the original yearly cost (£120.00) are visible on the card

### TC-4: Cancelled subscriptions are excluded from totals and visually distinct
- **Type:** Integration + Unit
- **Setup:** 2 subscriptions: one active £20/month, one cancelled £15/month
- **Steps:**
  1. *(Unit)* Run aggregation utility with these two subscriptions; assert result is £20.00, not £35.00
  2. *(Integration)* Render `DashboardPage` with these subscriptions; assert grand total displays £20.00
  3. Assert the cancelled subscription card has the "Cancelled" CSS class or badge element present
  4. Assert the active subscription card does not have the "Cancelled" styling
- **Expected Result:** Total is £20.00; cancelled card is visually distinguished; cancelled subscription does not contribute to any total

### TC-5: Free Trial subscriptions are included in totals and display trial end date
- **Type:** Integration
- **Setup:** 2 subscriptions: one active £10/month, one Free Trial £15/month with trialEndDate = "2025-08-01"
- **Steps:**
  1. Render `DashboardPage` with these subscriptions
  2. Assert grand total monthly cost displays £25.00
  3. Assert the trial subscription card displays a "Free Trial" badge
  4. Assert the trial subscription card displays the trial end date "2025-08-01" (or formatted equivalent)
- **Expected Result:** Trial subscription is included in the total (£25.00); badge and end date are visible on its card

### TC-6: Empty state is shown when no subscriptions exist
- **Type:** E2E
- **Setup:** User account with zero subscriptions; API returns empty array
- **Steps:**
  1. Navigate to the dashboard URL
  2. Assert the empty state message is visible (e.g. text "No subscriptions yet")
  3. Assert a "Add subscription" CTA button is present
  4. Assert the grand total monthly cost displays £0.00
  5. Assert the grand total yearly cost displays £0.00
- **Expected Result:** Empty state UI is shown; totals are £0.00; no category groups are rendered; CTA is actionable

### TC-7: Dashboard totals update immediately after a subscription is added
- **Type:** E2E
- **Setup:** Dashboard loaded with 1 active subscription at £20/month (grand total = £20.00)
- **Steps:**
  1. Navigate to the dashboard URL and confirm grand total is £20.00
  2. Add a new active subscription at £30/month via the create flow
  3. Return to / remain on the dashboard
  4. Assert the grand total monthly cost now displays £50.00
- **Expected Result:** Grand total updates to £50.00 without a full page reload; no stale data is displayed

## Technical Notes
- **API endpoint:** `GET /api/subscriptions` — must return `monthlyCostEquivalent` pre-calculated server-side to avoid repeating normalization logic across frontend components; normalization must use precise division (e.g. `Math.round((cost / 12) * 100) / 100`) to avoid floating-point drift
- **State management:** Subscriptions should be held in a top-level React context or a lightweight state store (e.g. Zustand or React Query cache) so that mutations (add/edit/delete) from any child component automatically invalidate and refetch the dashboard data, keeping totals in sync per AC-7
- **Aggregation logic:** Category grouping and total calculation should be implemented as pure utility functions (`groupByCategory`, `sumMonthlyCosts`, `calcGrandTotals`) that accept a subscription array and return derived data — this makes them unit-testable in isolation and reusable in story 6 (filter/sort)
- **Performance:** For MVP scope (expected <200 subscriptions per user), client-side aggregation is acceptable; no virtualization or pagination required at this stage
- **Currency:** MVP assumes single currency (£ GBP); currency symbol should be sourced from a single config constant to make future localization straightforward
- **Accessibility:** Category group headings must use semantic HTML (`<h2>` or `<h3>`); cost totals must have descriptive `aria-label` attributes (e.g. `aria-label="Total monthly cost: £40.00"`)

## Story Points
**Estimate:** 5 points
**Reasoning:** The read-only dashboard involves a moderately complex data-fetching and aggregation layer, multiple distinct UI components (category groups, cost summary, subscription cards with status variants, empty state), and normalization logic that must be precise and well-tested — but there are no form interactions, mutations, or complex user flows in this story.

## Definition of Done
- [ ] All Acceptance Criteria verified manually against the running application
- [ ] All Test Cases (TC-1 through TC-7) automated and passing in CI
- [ ] Code reviewed and approved by at least one other developer
- [ ] No console errors or TypeScript errors (`tsc --noEmit` passes cleanly)
- [ ] Dashboard grand totals verified with a test data set covering all three statuses and both billing cycles, confirming correct exclusion of cancelled subscriptions and correct normalization of yearly subscriptions
- [ ] Monetary values consistently formatted to 2 decimal places with currency symbol across all components on the dashboard