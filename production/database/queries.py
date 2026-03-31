# production/database/queries.py

import asyncpg
import os
import json
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fte_db")

async def get_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

async def resolve_customer(conn, email=None, phone=None, name=None):
    """Resolve customer by email or phone, or create a new one."""
    if email:
        customer = await conn.fetchrow("SELECT id FROM customers WHERE email = $1", email)
        if customer:
            return customer['id']
    
    if phone:
        customer = await conn.fetchrow("SELECT id FROM customers WHERE phone = $1", phone)
        if customer:
            return customer['id']
            
    # Create new if not found
    customer_id = await conn.fetchval(
        "INSERT INTO customers (email, phone, name) VALUES ($1, $2, $3) RETURNING id",
        email, phone, name
    )
    return customer_id

async def get_or_create_conversation(conn, customer_id, channel):
    """Get active conversation or create new one."""
    active = await conn.fetchrow(
        "SELECT id FROM conversations WHERE customer_id = $1 AND status = 'active' ORDER BY started_at DESC LIMIT 1",
        customer_id
    )
    if active:
        return active['id']
    
    return await conn.fetchval(
        "INSERT INTO conversations (customer_id, initial_channel, status) VALUES ($1, $2, 'active') RETURNING id",
        customer_id, channel
    )

async def store_message(conn, conversation_id, channel, direction, role, content, channel_message_id=None, latency_ms=None, tool_calls=[]):
    return await conn.execute(
        """INSERT INTO messages (conversation_id, channel, direction, role, content, channel_message_id, latency_ms, tool_calls)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        conversation_id, channel, direction, role, content, channel_message_id, latency_ms, json.dumps(tool_calls)
    )

async def create_ticket(conn, conversation_id, customer_id, channel, category=None, priority='medium'):
    return await conn.fetchval(
        """INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority, status)
           VALUES ($1, $2, $3, $4, $5, 'open') RETURNING id""",
        conversation_id, customer_id, channel, category, priority
    )

async def get_conversation_history(conn, customer_id, limit=20):
    return await conn.fetch(
        """SELECT m.role, m.content, m.channel, m.created_at
           FROM messages m
           JOIN conversations c ON m.conversation_id = c.id
           WHERE c.customer_id = $1
           ORDER BY m.created_at DESC LIMIT $2""",
        customer_id, limit
    )

async def update_ticket_status(conn, ticket_id, status, notes=None):
    await conn.execute(
        "UPDATE tickets SET status = $1, resolution_notes = $2 WHERE id = $3",
        status, notes, ticket_id
    )
