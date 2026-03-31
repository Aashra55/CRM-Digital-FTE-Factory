# mcp_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
from enum import Enum
from prototype import TechCorpAgent

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"

# Initialize our prototype agent
agent = TechCorpAgent(
    product_docs_path="context/product-docs.md",
    brand_voice_path="context/brand-voice.md",
    escalation_rules_path="context/escalation-rules.md"
)

server = Server("customer-success-fte")

@server.tool("search_knowledge_base")
async def search_kb(query: str) -> str:
    """Search product documentation for relevant information."""
    return agent._search_kb(query)

@server.tool("create_ticket")
async def create_ticket(
    customer_id: str, 
    issue: str, 
    priority: str,
    channel: Channel
) -> str:
    """Create a support ticket in the system with channel tracking."""
    # In a real system, this would write to a database
    return f"Ticket created for {customer_id} via {channel}. Issue: {issue}, Priority: {priority}"

@server.tool("get_customer_history")
async def get_customer_history(customer_id: str) -> str:
    """Get customer's interaction history across ALL channels."""
    conv = agent.conversation_manager.get_or_create(customer_id)
    return str(conv["history"])

@server.tool("send_response")
async def send_response(
    ticket_id: str,
    message: str,
    channel: Channel
) -> str:
    """Send response via the appropriate channel."""
    formatted = agent._format_response(message, channel.value)
    return f"Response sent to {ticket_id} via {channel}: {formatted}"

@server.tool("escalate_to_human")
async def escalate_to_human(ticket_id: str, reason: str) -> str:
    """Hand off complex issues to human support."""
    return f"Ticket {ticket_id} escalated. Reason: {reason}"

if __name__ == "__main__":
    server.run()
