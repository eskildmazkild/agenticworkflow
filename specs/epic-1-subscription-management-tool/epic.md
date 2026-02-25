<!-- GitHub Issue: #1 -->

# Subscription Management Tool

## Problem Statement
Individuals with multiple subscription services (streaming, SaaS, news, fitness, etc.) struggle to maintain a clear overview of what they are paying for, how much they are spending in total, and what the status of each subscription is. Without a centralized tool, users risk paying for forgotten subscriptions, missing trial-to-paid conversions, or losing track of cancellation dates. The business impact is financial waste and lack of control over recurring personal or household expenses.

## Goal
Deliver a web-based subscription management tool that gives users a complete, categorized overview of all their subscriptions — active, cancelled, or in trial — with clear cost summaries per category, month, and year, so they can make informed decisions about their spending.

## Success Metrics
- Users can view the total monthly and yearly cost of all subscriptions, broken down by category, within 2 clicks of logging in
- 100% of subscription statuses (active, free trial, cancelled with end date) are accurately reflected in the overview at all times
- Users can add, edit, or cancel a subscription in under 60 seconds

## Scope

### In Scope
- Creating, editing, and deleting subscriptions with relevant metadata (name, category, cost, billing cycle, status, dates)
- Categorization of subscriptions (e.g. Streaming, Software, News, Fitness, Other)
- Subscription status tracking: Active, Free Trial (with trial end date), Cancelled (with cancellation date and last active date)
- Dashboard overview with cost totals per category, per month, and per year
- Visual distinction between active, trial, and cancelled subscriptions
- Filtering and sorting of subscriptions by status, category, and cost
- Support for monthly and yearly billing cycles with normalized cost calculation (monthly equivalent)

### Out of Scope
- Automatic detection or import of subscriptions from bank statements or email
- Payment processing or billing integrations
- Multi-user/household sharing of subscription data
- Mobile native app (iOS/Android) — web only
- Budget goal setting or spending alerts/notifications
- Currency conversion for subscriptions in foreign currencies
- Historical price change tracking per subscription

## User Personas
| Persona | Role | Key Need |
|---------|------|----------|
| Alex | Primary user — individual managing personal subscriptions | A single place to see all subscriptions, their costs, and statuses without spreadsheets |
| Jordan | Household manager tracking shared family subscriptions | Clear category totals and visibility into which services are still active vs. cancelled |

## User Stories
List the user stories that together fulfill this epic. Each story should be independently deliverable.

1. View subscription dashboard with cost totals per category, month, and year
2. Create a new subscription with full metadata (name, category, cost, billing cycle, start date, status)
3. Edit an existing subscription's details and billing information
4. Manage subscription status — mark as Free Trial, Active, or Cancelled with relevant dates
5. Delete a subscription from the system
6. Filter and sort the subscription list by status, category, and cost
7. View a detailed summary for a single subscription including full status history and cost breakdown

## Technical Risks & Considerations
- **Billing cycle normalization:** Monthly and yearly prices must be consistently normalized to a monthly equivalent for accurate cross-subscription cost comparisons — rounding and precision must be handled carefully
- **Date logic complexity:** Free trial end dates, cancellation dates, and "last active" dates must be validated against each other to prevent invalid state combinations (e.g. cancellation date before start date)
- **Status state machine:** Subscription status transitions (Active → Cancelled, Trial → Active, Trial → Cancelled) should follow a defined state machine to prevent inconsistent data
- **Frontend state management:** The dashboard aggregates data across all subscriptions in real time — filtering, sorting, and totals must stay in sync without performance degradation as the subscription list grows
- **Data persistence:** Decisions needed on whether data is user-account-scoped (requires authentication) or stored locally (e.g. localStorage/IndexedDB) — this impacts architecture significantly

## Dependencies
- Authentication/user account system if data is to be persisted per user in a backend database
- REST API backend capable of storing and retrieving subscription records with filtering and sorting support
- Decision on supported currencies (single-currency MVP assumed)

## Definition of Done (Epic Level)
- [ ] All user stories completed and accepted by PO
- [ ] End-to-end tests passing for all critical flows (create, edit, cancel, delete, dashboard totals)
- [ ] Dashboard correctly calculates and displays monthly/yearly totals per category and in aggregate, verified with test data covering all billing cycles and statuses
- [ ] All subscription statuses (Active, Free Trial, Cancelled) are visually distinct and display correct associated dates
- [ ] Application is accessible and functional in latest versions of Chrome, Firefox, and Safari