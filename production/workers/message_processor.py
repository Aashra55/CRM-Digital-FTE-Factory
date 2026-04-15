# production/workers/message_processor.py

import asyncio
import logging
from kafka_client import FTEKafkaConsumer, FTEKafkaProducer, TOPICS
from agents import Runner
from agent.customer_success_agent import customer_success_agent
from agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
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
        
        # Start Gmail polling in background (Commented out to save API quota)
        # asyncio.create_task(self.gmail_polling_loop())
        
        consumer = FTEKafkaConsumer(
            topics=[TOPICS['tickets_incoming']],
            group_id='fte-message-processor'
        )
        await consumer.start()
        
        logger.info("Message processor started, listening for tickets...")
        await consumer.consume(self.process_message)

    async def gmail_polling_loop(self):
        """Periodically poll Gmail for new messages."""
        logger.info("Gmail polling loop started")
        while True:
            try:
                new_messages = await self.gmail.poll_messages()
                for msg in new_messages:
                    logger.info(f"Found new Gmail message from {msg['customer_email']}")
                    await self.producer.publish(TOPICS['tickets_incoming'], msg)
            except Exception as e:
                logger.error(f"Error in Gmail polling loop: {e}")
            
            await asyncio.sleep(60) # Poll every minute
    
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
                
                # 4. Run agent with dynamic context in prompt
                dynamic_instructions = f"{CUSTOMER_SUCCESS_SYSTEM_PROMPT}\n\nCURRENT CONTEXT:\n- customer_id: {customer_id}\n- channel: {channel.value}"
                
                # We update the agent instructions temporarily for this run
                customer_success_agent.instructions = dynamic_instructions
                
                # Retry loop for agent execution
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        result = await Runner.run(
                            starting_agent=customer_success_agent,
                            input=message['content'],
                            context={
                                'customer_id': str(customer_id),
                                'conversation_id': str(conversation_id),
                                'channel': channel.value,
                                'ticket_subject': message.get('subject', 'Support Request')
                            }
                        )
                        break
                    except Exception as e:
                        if "503" in str(e) or "429" in str(e):
                            if attempt == max_retries - 1:
                                raise
                            wait = (10 * (attempt + 1))
                            logger.warning(f"Agent failed with {e}, retrying in {wait}s...")
                            await asyncio.sleep(wait)
                        else:
                            raise
                
                # 6. Calculate latency
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # 7. Store agent response
                # Note: RunResult might not have .tool_calls directly, checking safely
                tc_data = []
                if hasattr(result, 'tool_calls'):
                    tc_data = [tc.to_dict() for tc in result.tool_calls]
                
                await store_message(
                    conn, 
                    conversation_id, 
                    channel.value, 
                    'outbound', 
                    'agent', 
                    result.final_output, 
                    latency_ms=int(latency_ms),
                    tool_calls=tc_data
                )
                
                # 8. Send response via channel
                await self.send_channel_response(channel, message, result.final_output)
                
                # 9. Publish metrics
                await self.producer.publish(TOPICS['metrics'], {
                    'event_type': 'message_processed',
                    'channel': channel.value,
                    'latency_ms': latency_ms,
                    'tool_calls_count': len(tc_data)
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
