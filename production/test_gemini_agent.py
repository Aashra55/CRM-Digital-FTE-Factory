# production/test_gemini_agent.py

import asyncio
import os
from agent.customer_success_agent import customer_success_agent
from agents import Runner

async def test_agent():
    print("--- Testing TechCorp FTE with Gemini API ---")
    
    # Check if key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not found in environment!")
        return

    # Simulate a user message
    user_query = "Hey, I'm having trouble connecting my GitHub integration. Can you help?"
    
    print(f"User Query: {user_query}")
    print("Processing...")

    result = await Runner.run(
        starting_agent=customer_success_agent,
        input=[{"role": "user", "content": user_query}],
        context={"channel": "whatsapp", "customer_id": "test-user-99"}
    )
    
    print("\n--- FTE Response ---")
    print(result.final_output)
    print("\n--- Tool Calls Used ---")
    for call in result.tool_calls:
        print(f"- Tool: {call.tool_name}, Args: {call.args}")

if __name__ == "__main__":
    asyncio.run(test_agent())
