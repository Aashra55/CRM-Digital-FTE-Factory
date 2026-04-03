# production/channels/gmail_handler.py

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import email
from email.mime.text import MIMEText
from datetime import datetime
import json
import os

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailHandler:
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = 'token.json'
        self.service = self._authenticate()
        
    def _authenticate(self):
        """Authenticates and returns the Gmail service."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = self._get_new_creds()
            else:
                creds = self._get_new_creds()
            
            if creds:
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())

        if not creds:
            print("Warning: Gmail authentication failed. Mode: MOCK")
            return None

        return build('gmail', 'v1', credentials=creds)

    def _get_new_creds(self):
        """Starts the OAuth flow to get new credentials."""
        if not os.path.exists(self.credentials_path):
            print(f"Error: {self.credentials_path} not found.")
            return None
        
        try:
            # Using fixed redirect URI for Docker compatibility
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, 
                SCOPES
            )
            flow.redirect_uri = 'http://localhost:8080/'
            
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            
            print("\n" + "="*60)
            print("GMAIL AUTHENTICATION REQUIRED")
            print(f"1. Open this URL: {auth_url}")
            print("2. Authorize the app.")
            print("3. Copy the 'code' from the failing URL and put it in 'auth_code.txt'.")
            print("="*60 + "\n")
            
            import time
            auth_code_file = 'auth_code.txt'
            for _ in range(60): # Wait 5 minutes
                if os.path.exists(auth_code_file):
                    with open(auth_code_file, 'r') as f:
                        code = f.read().strip()
                    os.remove(auth_code_file)
                    flow.fetch_token(code=code)
                    return flow.credentials
                time.sleep(5)
                
            return None
        except Exception as e:
            print(f"Error during OAuth flow: {e}")
            return None
        
    async def setup_push_notifications(self, topic_name: str):
        if not self.service: return {"status": "mock_setup"}
        request = {'labelIds': ['INBOX'], 'topicName': topic_name, 'labelFilterAction': 'include'}
        return self.service.users().watch(userId='me', body=request).execute()
    
    async def process_notification(self, pubsub_message: dict) -> list:
        if not self.service: return []
        history_id = pubsub_message.get('historyId')
        try:
            history = self.service.users().history().list(userId='me', startHistoryId=history_id, historyTypes=['messageAdded']).execute()
        except Exception as e:
            print(f"Error fetching history: {e}"); return []
        messages = []
        for record in history.get('history', []):
            for msg_added in record.get('messagesAdded', []):
                message = await self.get_message(msg_added['message']['id'])
                messages.append(message)
        return messages
    
    async def get_message(self, message_id: str) -> dict:
        if not self.service: return {}
        try:
            msg = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            body = self._extract_body(msg['payload'])
            return {
                'channel': 'email', 'channel_message_id': message_id,
                'customer_email': self._extract_email(headers.get('From', '')),
                'subject': headers.get('Subject', ''), 'content': body,
                'received_at': datetime.utcnow().isoformat(), 'thread_id': msg.get('threadId')
            }
        except Exception as e:
            print(f"Error getting message {message_id}: {e}"); return {}
    
    def _extract_body(self, payload: dict) -> str:
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'parts' in part:
                    res = self._extract_body(part)
                    if res: return res
        return ''
    
    def _extract_email(self, from_header: str) -> str:
        import re
        match = re.search(r'<(.+?)>', from_header)
        return match.group(1) if match else from_header
    
    async def send_reply(self, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        if not self.service:
            print(f"Mock Send Email to {to_email}: {body[:50]}..."); return {'channel_message_id': 'mock-sent-id', 'delivery_status': 'sent'}
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = f"Re: {subject}" if not subject.lower().startswith('re:') else subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        send_request = {'raw': raw}
        if thread_id: send_request['threadId'] = thread_id
        try:
            result = self.service.users().messages().send(userId='me', body=send_request).execute()
            return {'channel_message_id': result['id'], 'delivery_status': 'sent'}
        except Exception as e:
            print(f"Error sending email: {e}"); return {'delivery_status': 'failed', 'error': str(e)}

    async def poll_messages(self) -> list:
        if not self.service: return []
        try:
            results = self.service.users().messages().list(userId='me', q='is:unread label:INBOX').execute()
            messages_summary = results.get('messages', [])
            if not messages_summary: return []
            parsed_messages = []
            for msg_summary in messages_summary:
                message = await self.get_message(msg_summary['id'])
                if message:
                    parsed_messages.append(message)
                    self.service.users().messages().batchModify(userId='me', body={'ids': [msg_summary['id']], 'removeLabelIds': ['UNREAD']}).execute()
            return parsed_messages
        except Exception as e:
            print(f"Error polling Gmail: {e}"); return []
