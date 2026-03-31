# production/workers/message_processor.py

import asyncio
import logging
from kafka_client import FTEKafkaConsumer, FTEKafkaProducer, TOPICS
from agents import Runner
from agent.customer_success_agent import customer_success_agent
from agent.tools import Channel
from channels.gmail_handler import GmailHandler
from channels.whatsapp_handler import WhatsAppHandler
from database.queries import get_db_pool, resolve_customer, get_or_create_conversation, store_message
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedMessageProcessor:
    def __init__(self):
        self.gmail = GmailHandler()
        self.whatsapp = WhatsAppHandler()
        self.producer = FTEKafkaProducer()
        self.pool = None
        
    async def start(self):
        """Start the message processor."""
        self.pool = await get_db_pool()
        await self.producer.start()
        
        consumer = FTEKafkaConsumer(
            topics=[TOPICS['tickets_incoming']],
            group_id='fte-message-processor'
        )
        await consumer.start()
        
        logger.info("Message processor started, listening for tickets...")
        await consumer.consume(self.process_message)
    
    async def process_message(self, topic, message):
        """Process a single incoming message from any channel."""
        try:
            start_time = datetime.utcnow()
            channel = Channel(message['channel'])
            
            async with self.pool.acquire() as conn:
                # 1. Resolve customer
                customer_id = await resolve_customer(
                    conn, 
                    email=message.get('customer_email'), 
                    phone=message.get('customer_phone'),
                    name=message.get('customer_name')
                )
                
                # 2. Get/Create conversation
                conversation_id = await get_or_create_conversation(conn, customer_id, channel.value)
                
                # 3. Store incoming message
                await store_message(
                    conn, 
                    conversation_id, 
                    channel.value, 
                    'inbound', 
                    'customer', 
                    message['content'], 
                    message.get('channel_message_id')
                )
                
                # 4. Load conversation history (for agent)
                history_data = await conn.fetch(
                    "SELECT role, content FROM messages WHERE conversation_id = $1 ORDER BY created_at ASC",
                    conversation_id
                )
                messages = [{"role": h['role'], "content": h['content']} for h in history_data]
                
                # 5. Run agent
                runner = Runner()
                result = await runner.run(
                    agent=customer_success_agent,
                    messages=messages,
                    context={
                        'customer_id': str(customer_id),
                        'conversation_id': str(conversation_id),
                        'channel': channel.value,
                        'ticket_subject': message.get('subject', 'Support Request')
                    }
                )
                
                # 6. Calculate latency
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # 7. Store agent response
                await store_message(
                    conn, 
                    conversation_id, 
                    channel.value, 
                    'outbound', 
                    'agent', 
                    result.final_output, 
                    latency_ms=int(latency_ms),
                    tool_calls=[tc.to_dict() for tc in result.tool_calls]
                )
                
                # 8. Send response via channel
                await self.send_channel_response(channel, message, result.final_output)
                
                # 9. Publish metrics
                await self.producer.publish(TOPICS['metrics'], {
                    'event_type': 'message_processed',
                    'channel': channel.value,
                    'latency_ms': latency_ms,
                    'tool_calls_count': len(result.tool_calls)
                })
                
                logger.info(f"Processed {channel.value} message for customer {customer_id}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # In a real app, handle error and maybe notify humans

    async def send_channel_response(self, channel, original_message, response_text):
        """Send response back through the original channel."""
        if channel == Channel.EMAIL:
            await self.gmail.send_reply(
                to_email=original_message['customer_email'],
                subject=original_message.get('subject', 'Support Response'),
                body=response_text,
                thread_id=original_message.get('thread_id')
            )
        elif channel == Channel.WHATSAPP:
            await self.whatsapp.send_message(
                to_phone=original_message['customer_phone'],
                body=response_text
            )
        # Web form responses are usually fetched via polling or websocket, or sent via email notification
        elif channel == Channel.WEB_FORM:
            await self.gmail.send_reply(
                to_email=original_message['customer_email'],
                subject=f"RE: {original_message.get('subject', 'Support Request')}",
                body=f"Hi {original_message.get('customer_name', 'there')},\n\nWe have a response for your support request:\n\n{response_text}"
            )

if __name__ == "__main__":
    processor = UnifiedMessageProcessor()
    asyncio.run(processor.start())
