# production/kafka_client.py

import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from datetime import datetime
import os
import asyncio

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Topic definitions for multi-channel FTE
TOPICS = {
    # Incoming tickets from all channels
    'tickets_incoming': 'fte.tickets.incoming',
    
    # Channel-specific inbound
    'email_inbound': 'fte.channels.email.inbound',
    'whatsapp_inbound': 'fte.channels.whatsapp.inbound',
    'webform_inbound': 'fte.channels.webform.inbound',
    
    # Channel-specific outbound
    'email_outbound': 'fte.channels.email.outbound',
    'whatsapp_outbound': 'fte.channels.whatsapp.outbound',
    
    # Escalations
    'escalations': 'fte.escalations',
    
    # Metrics and monitoring
    'metrics': 'fte.metrics',
    
    # Dead letter queue for failed processing
    'dlq': 'fte.dlq'
}


class FTEKafkaProducer:
    def __init__(self):
        self.producer = None
        
    async def start(self):
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
        except Exception as e:
            print(f"Failed to start Kafka Producer: {e}")
            self.producer = None
            raise
        
    async def stop(self):
        if self.producer:
            await self.producer.stop()
        
    async def publish(self, topic: str, event: dict):
        if not self.producer:
            print(f"Warning: Kafka producer not started, cannot publish to {topic}")
            return
        event["timestamp"] = datetime.utcnow().isoformat()
        try:
            # Add a timeout to prevent hanging the entire request
            await asyncio.wait_for(self.producer.send_and_wait(topic, event), timeout=5.0)
        except asyncio.TimeoutError:
            print(f"Timeout error publishing to {topic}")
        except Exception as e:
            print(f"Error publishing to {topic}: {e}")


class FTEKafkaConsumer:
    def __init__(self, topics: list, group_id: str):
        self.topics = topics
        self.group_id = group_id
        self.consumer = None
        
    async def start(self):
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            await self.consumer.start()
        except Exception as e:
            print(f"Failed to start Kafka Consumer: {e}")
        
    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
        
    async def consume(self, handler):
        if not self.consumer:
            print("Warning: Kafka consumer not started, skipping consume")
            return
            
        try:
            async for msg in self.consumer:
                await handler(msg.topic, msg.value)
        except Exception as e:
             print(f"Consumer loop error: {e}")
