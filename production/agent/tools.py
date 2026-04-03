# production/agent/tools.py

from agents import function_tool
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import asyncpg
import os
import json
from database.queries import create_ticket as db_create_ticket, get_conversation_history, update_ticket_status

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fte_db")

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"

class KnowledgeSearchInput(BaseModel):
    query: str = Field(..., description="The search query for the knowledge base.")
    max_results: int = Field(5, description="Maximum number of results to return.")

class TicketInput(BaseModel):
    customer_id: str = Field(..., description="The unique ID of the customer (must be a valid UUID).")
    issue: str = Field(..., description="Brief description of the issue.")
    priority: str = Field("medium", description="Priority level: low, medium, high.")
    category: Optional[str] = Field(None, description="Category of the issue.")
    channel: Channel = Field(..., description="The channel the ticket originated from.")

class ResponseInput(BaseModel):
    ticket_id: str = Field(..., description="The ID of the ticket being responded to.")
    message: str = Field(..., description="The response message.")
    channel: Channel = Field(..., description="The channel to send the response through.")

@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information."""
    # In production, this would use pgvector
    # For now, we mock the result based on some hardcoded patterns
    query = input.query.lower()
    if "password" in query:
        return "Password reset: Go to login, click Forgot Password, enter email, follow reset link."
    if "github" in query:
        return "GitHub integration: Settings > Integrations > Disconnect > Connect > Authorize."
    if "project" in query:
        return "Projects: Login > Create Project > Name/Desc > Invite Team > Create Tasks."
    return "No specific match found. Please provide more details or ask about password, github, or projects."

@function_tool
async def create_ticket(input: TicketInput) -> str:
    """Create a support ticket for tracking."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        # In a real tool, conversation_id should be passed in context
        # Here we mock/assume a conversation_id for simplicity of tool definition
        ticket_id = await db_create_ticket(conn, None, input.customer_id, input.channel.value, input.category, input.priority)
        await conn.close()
        return f"Ticket successfully created. Ticket ID: {ticket_id}"
    except Exception as e:
        return f"Error creating ticket: {str(e)}"

@function_tool
async def get_customer_history(customer_id: str) -> str:
    """Get customer's complete interaction history across ALL channels."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        history = await get_conversation_history(conn, customer_id)
        await conn.close()
        if not history:
            return "No previous interaction history found for this customer."
        
        formatted = []
        for h in history:
            formatted.append(f"[{h['created_at'].strftime('%Y-%m-%d %H:%M')}] {h['role']} via {h['channel']}: {h['content'][:100]}...")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error fetching history: {str(e)}"

@function_tool
async def escalate_to_human(ticket_id: str, reason: str) -> str:
    """Escalate conversation to human support."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await update_ticket_status(conn, ticket_id, 'escalated', reason)
        return f"Ticket {ticket_id} has been escalated to human support. Reason: {reason}"
    finally:
        await conn.close()

@function_tool
async def send_response(input: ResponseInput) -> str:
    """Send response to customer via their preferred channel. 
    This tool signals that the agent has finished thinking and is ready to reply."""
    # This is often handled by the runner/worker after the tool is called
    return f"Response queued for {input.channel}: {input.message}"
