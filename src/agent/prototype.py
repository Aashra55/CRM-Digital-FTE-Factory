import json
import os

class ConversationManager:
    def __init__(self):
        self.conversations = {}

    def get_or_create(self, customer_id):
        if customer_id not in self.conversations:
            self.conversations[customer_id] = {
                "history": [],
                "sentiment_trend": [],
                "topics": set(),
                "status": "active",
                "channel_switches": 0,
                "original_channel": None
            }
        return self.conversations[customer_id]

    def add_message(self, customer_id, message, channel, role):
        conv = self.get_or_create(customer_id)
        if not conv["original_channel"]:
            conv["original_channel"] = channel
        elif conv["original_channel"] != channel:
            conv["channel_switches"] += 1
            conv["original_channel"] = channel # Update current channel

        conv["history"].append({"role": role, "content": message, "channel": channel})
        
        if role == "customer":
            sentiment = self._analyze_sentiment(message)
            conv["sentiment_trend"].append(sentiment)
            topic = self._identify_topic(message)
            if topic:
                conv["topics"].add(topic)

    def _analyze_sentiment(self, message):
        # Very simple sentiment analysis for prototype
        positive_words = ["happy", "great", "thanks", "good", "love", "help"]
        negative_words = ["angry", "bad", "slow", "broken", "sucks", "annoying", "hate", "refund"]
        
        score = 0.5 # Neutral
        lower_message = message.lower()
        for word in positive_words:
            if word in lower_message:
                score += 0.1
        for word in negative_words:
            if word in lower_message:
                score -= 0.1
        
        return max(0, min(1, score))

    def _identify_topic(self, message):
        # Simple topic identification
        lower_message = message.lower()
        if "password" in lower_message or "account" in lower_message:
            return "Account Management"
        if "github" in lower_message or "integration" in lower_message:
            return "Integrations"
        if "billing" in lower_message or "refund" in lower_message or "pricing" in lower_message:
            return "Billing"
        if "project" in lower_message or "task" in lower_message:
            return "Project Management"
        return "General"

class TechCorpAgent:
    def __init__(self, product_docs_path, brand_voice_path, escalation_rules_path):
        self.product_docs = self._load_file(product_docs_path)
        self.brand_voice = self._load_file(brand_voice_path)
        self.escalation_rules = self._load_file(escalation_rules_path)
        self.conversation_manager = ConversationManager()

    def _load_file(self, path):
        with open(path, 'r') as f:
            return f.read()

    def process_message(self, message, channel, customer_id):
        # 1. Update memory
        self.conversation_manager.add_message(customer_id, message, channel, "customer")
        conv = self.conversation_manager.get_or_create(customer_id)
        
        # 2. Normalize message
        message = message.strip()
        
        # 3. Search product docs (using context from history if needed)
        kb_results = self._search_kb(message)
        
        # 4. Decide on escalation (include sentiment analysis)
        current_sentiment = conv["sentiment_trend"][-1]
        should_escalate, reason = self._check_escalation(message, kb_results, current_sentiment)
        
        # 5. Generate response
        if should_escalate:
            response = self._generate_escalation_message(reason)
            conv["status"] = "escalated"
        else:
            response = self._generate_kb_response(kb_results)
            conv["status"] = "pending" # Waiting for user feedback
        
        # 6. Update memory with agent response
        self.conversation_manager.add_message(customer_id, response, channel, "agent")
        
        # 7. Format response for channel
        formatted_response = self._format_response(response, channel)
        
        return {
            "customer_id": customer_id,
            "channel": channel,
            "response": formatted_response,
            "escalated": should_escalate,
            "escalation_reason": reason,
            "sentiment": current_sentiment,
            "topics": list(conv["topics"]),
            "status": conv["status"]
        }

    def _search_kb(self, query):
        # Basic keyword-based search for prototype
        keywords = query.lower().split()
        relevant_sections = []
        for line in self.product_docs.split('\n'):
            if any(kw in line.lower() for kw in keywords):
                relevant_sections.append(line)
        return "\n".join(relevant_sections[:5])

    def _check_escalation(self, message, kb_results, sentiment):
        # Enhanced escalation logic with sentiment
        lower_message = message.lower()
        if sentiment < 0.4:
            return True, f"Negative sentiment detected ({sentiment:.2f})"
        if "refund" in lower_message or "pricing" in lower_message:
            return True, "Pricing/Refund inquiry"
        if not kb_results:
            return True, "No relevant information found"
        if "human" in lower_message or "agent" in lower_message:
            return True, "Customer requested a human agent"
        return False, None

    def _generate_kb_response(self, kb_results):
        if not kb_results:
            return "I'm sorry, I couldn't find information about that. Let me connect you with a human agent."
        return f"Based on our documentation:\n{kb_results}"

    def _generate_escalation_message(self, reason):
        return f"I've escalated your issue to our support team due to: {reason}. A human agent will be with you shortly."

    def _format_response(self, response, channel):
        if channel == "email":
            return f"Dear Customer,\n\n{response}\n\nBest regards,\nTechCorp Support Team"
        elif channel == "whatsapp":
            # Shorten and make more conversational
            return f"Hi! {response} Let me know if you need more help!"
        else: # web_form
            return f"Hi,\n\n{response}\n\nTechCorp Support Team"

# Example Usage
if __name__ == "__main__":
    agent = TechCorpAgent(
        product_docs_path="context/product-docs.md",
        brand_voice_path="context/brand-voice.md",
        escalation_rules_path="context/escalation-rules.md"
    )

    test_scenarios = [
        {"message": "How do I reset my password?", "channel": "email", "customer_id": "C001"},
        {"message": "I'm really angry, this product is bad!", "channel": "whatsapp", "customer_id": "C004"},
        {"message": "I want a refund", "channel": "whatsapp", "customer_id": "C003"},
        {"message": "How do I connect to GitHub?", "channel": "web_form", "customer_id": "C002"}
    ]

    for scenario in test_scenarios:
        result = agent.process_message(scenario["message"], scenario["channel"], scenario["customer_id"])
        print(f"--- Channel: {result['channel']} ---")
        print(f"Sentiment: {result['sentiment']:.2f}")
        print(f"Topics: {result['topics']}")
        print(f"Status: {result['status']}")
        print(f"Response: {result['response']}")
        print(f"Escalated: {result['escalated']} (Reason: {result['escalation_reason']})")
        print("-" * 30)
