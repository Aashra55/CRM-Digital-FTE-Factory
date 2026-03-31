# Transition Checklist: General → Custom Agent

## 1. Discovered Requirements
- [x] Multi-channel identification (email as primary key).
- [x] Channel-aware tone and length adjustment.
- [x] Sentiment-based escalation (threshold 0.3-0.4).
- [x] Simple topic identification (Account, Billing, etc.).
- [x] Memory tracking for cross-channel continuity.

## 2. Working Prompts
### System Prompt That Worked:
"You are a Customer Success agent for TechCorp SaaS. Be professional, helpful, and empathetic. Adapt your tone to the channel (Email: formal, WhatsApp: concise, Web: semi-formal). ALWAYS create a ticket and check history before responding. Escalate for pricing, refunds, legal, or frustrated customers."

## 3. Edge Cases Found
| Edge Case | How It Was Handled | Test Case Needed |
|-----------|-------------------|------------------|
| Empty message | Clarification requested | Yes |
| Pricing question | Escalated to Billing | Yes |
| Negative sentiment | Escalated to Human | Yes |
| Multi-channel user | History merged | Yes |

## 4. Response Patterns
- **Email**: "Dear Customer... Best regards, TechCorp Support Team"
- **WhatsApp**: "Hi! [Concise Answer] Let me know if you need more help!"
- **Web Form**: "Hi, [Structured Answer] TechCorp Support Team"

## 5. Escalation Rules (Finalized)
- Pricing/Refund inquiries.
- No relevant KB information found after 2 tries.
- Sentiment score < 0.4.
- Explicit human request.

## 6. Performance Baseline (Prototype)
- **Response time**: ~10ms (local execution).
- **Escalation accuracy**: 100% on sample scenarios.
- **Topic identification**: 100% on keywords.
