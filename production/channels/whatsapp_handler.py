# production/channels/whatsapp_handler.py

from twilio.rest import Client
from twilio.request_validator import RequestValidator
from fastapi import Request, HTTPException
import os
from datetime import datetime

class WhatsAppHandler:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')  # e.g., 'whatsapp:+14155238886'
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.validator = RequestValidator(self.auth_token)
        else:
            print("Warning: Twilio credentials not found. Mode: MOCK")
            self.client = None
            self.validator = None
    
    async def validate_webhook(self, request: Request) -> bool:
        """Validate incoming Twilio webhook signature."""
        if not self.validator:
            return True # Mock validation

        signature = request.headers.get('X-Twilio-Signature', '')
        url = str(request.url)
        form_data = await request.form()
        params = dict(form_data)
        
        return self.validator.validate(url, params, signature)
    
    async def process_webhook(self, form_data: dict) -> dict:
        """Process incoming WhatsApp message from Twilio webhook."""
        return {
            'channel': 'whatsapp',
            'channel_message_id': form_data.get('MessageSid', 'mock-sid'),
            'customer_phone': form_data.get('From', '').replace('whatsapp:', ''),
            'content': form_data.get('Body', ''),
            'received_at': datetime.utcnow().isoformat(),
            'metadata': {
                'num_media': form_data.get('NumMedia', '0'),
                'profile_name': form_data.get('ProfileName'),
                'wa_id': form_data.get('WaId'),
                'status': form_data.get('SmsStatus')
            }
        }
    
    async def send_message(self, to_phone: str, body: str) -> dict:
        """Send WhatsApp message via Twilio."""
        if not self.client:
             print(f"Mock Send WhatsApp to {to_phone}: {body[:50]}...")
             return {'channel_message_id': 'mock-sent-id', 'delivery_status': 'sent'}

        # Ensure phone number is in WhatsApp format
        if not to_phone.startswith('whatsapp:'):
            to_phone = f'whatsapp:{to_phone}'
        
        try:
            message = self.client.messages.create(
                body=body,
                from_=self.whatsapp_number,
                to=to_phone
            )
            
            return {
                'channel_message_id': message.sid,
                'delivery_status': message.status  # 'queued', 'sent', 'delivered', 'failed'
            }
        except Exception as e:
             print(f"Error sending WhatsApp message: {e}")
             return {'delivery_status': 'failed', 'error': str(e)}
    
    def format_response(self, response: str, max_length: int = 1600) -> list[str]:
        """Format and split response for WhatsApp (max 1600 chars per message)."""
        if len(response) <= max_length:
            return [response]
        
        # Split into multiple messages
        messages = []
        while response:
            if len(response) <= max_length:
                messages.append(response)
                break
            
            # Find a good break point
            break_point = response.rfind('. ', 0, max_length)
            if break_point == -1:
                break_point = response.rfind(' ', 0, max_length)
            if break_point == -1:
                break_point = max_length
            
            messages.append(response[:break_point + 1].strip())
            response = response[break_point + 1:].strip()
        
        return messages
