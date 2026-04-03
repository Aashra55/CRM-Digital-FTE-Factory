# production/agent/customer_success_agent.py

from agents import Agent, Runner, OpenAIChatCompletionsModel
from .tools import search_knowledge_base, create_ticket, get_customer_history, escalate_to_human, send_response
from .prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
import os
from openai import AsyncOpenAI

# Gemini API configuration via OpenAI compatibility layer
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Create a custom client pointing to Google's OpenAI-compatible endpoint
# Note: Gemini 1.5 Flash is excellent for FTE agents (fast and free/cheap)
custom_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Wrap the client in the SDK's model class
gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=custom_client
)

# Define the Customer Success Agent
customer_success_agent = Agent(
    name="Customer Success FTE",
    model=gemini_model, # Using the wrapped Gemini model
    instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
    tools=[
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        escalate_to_human,
        send_response
    ]
)

if __name__ == "__main__":
    import asyncio
    
    async def main():
        runner = Runner()
        # Test run with Gemini
        result = await runner.run(
            agent=customer_success_agent,
            input="How do I reset my password?",
        )
        print(f"Gemini FTE Output: {result.final_output}")

    asyncio.run(main())
