# Discovery Log: TechCorp Customer Success FTE

## Exercise 1.1: Initial Exploration (2026-03-18)

### Intent
Build a Customer Success AI agent for TechCorp SaaS that handles inquiries from Email, WhatsApp, and Web Form, answers from product docs, escalates when necessary, and tracks all interactions.

### Sample Ticket Analysis
Based on the `sample-tickets.json`, I've identified several patterns:

#### Channel Patterns
- **Email (T001, T004)**: Tends to be more formal and includes a subject line. Customers provide more detail.
- **WhatsApp (T002, T005)**: More conversational and concise. Users expect quick answers and use less formal language.
- **Web Form (T003, T006)**: Semi-formal. Usually includes a subject and a specific category or priority (as seen in T006's "Urgent" subject).

#### Topic Patterns
- **Product Questions**: Questions about how to use features like creating projects (T004) or connecting GitHub (T002).
- **Technical Issues**: Reports of data not showing (T005) or being locked out (T006).
- **Billing**: Inquiries about charges or plans (T003).
- **Account Management**: Password resets (T001).

#### Escalation Potential
- **T003 (Billing)**: Pricing/refund inquiry. Potential escalation.
- **T006 (Urgent Account Lockout)**: High urgency and potential frustration. Likely escalation.

### Initial Observations
- The agent needs to be channel-aware to adjust its tone and length.
- A unified customer identity is crucial, as seen with emails being used as primary keys.
- Sentiment analysis will be key for proactive escalation, especially for frustrated customers.

### Questions for Clarification
- What are the specific sentiment score thresholds for each channel?
- How should we handle cases where a customer uses a different email address for each channel?
- Is there a specific format for escalating tickets to human agents (e.g., Slack, Email)?
