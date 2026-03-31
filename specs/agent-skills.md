# Agent Skills Manifest: TechCorp Customer Success FTE

## 1. Knowledge Retrieval Skill
- **Purpose**: Find relevant product documentation to answer customer questions.
- **When to use**: Whenever a customer asks a how-to or product feature question.
- **Inputs**: `query` (string)
- **Outputs**: `snippets` (list of relevant document sections)
- **Tool**: `search_knowledge_base`

## 2. Sentiment Analysis Skill
- **Purpose**: Assess the emotional tone of customer messages to identify frustration.
- **When to use**: Every incoming customer message.
- **Inputs**: `message` (string)
- **Outputs**: `sentiment_score` (0.0 - 1.0), `confidence` (float)
- **Integrated in**: `process_message` logic.

## 3. Escalation Decision Skill
- **Purpose**: Determine if a ticket needs human intervention based on rules and sentiment.
- **When to use**: After every message processing step.
- **Inputs**: `message` (string), `kb_results` (string), `sentiment` (float)
- **Outputs**: `should_escalate` (boolean), `reason` (string)
- **Tool**: `escalate_to_human`

## 4. Channel Adaptation Skill
- **Purpose**: Format the agent's response according to the specific channel's tone and constraints.
- **When to use**: Before sending any response to the customer.
- **Inputs**: `response` (string), `channel` (string)
- **Outputs**: `formatted_response` (string)
- **Tool**: `send_response` (internal formatting)

## 5. Customer Identification Skill
- **Purpose**: Unified customer tracking across multiple communication channels.
- **When to use**: On every incoming message.
- **Inputs**: `metadata` (email, phone, etc.)
- **Outputs**: `customer_id` (string), `merged_history` (list)
- **Integrated in**: `ConversationManager`.
