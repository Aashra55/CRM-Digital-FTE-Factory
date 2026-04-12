# production/api/main.py

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
from datetime import datetime
import os
import json
import asyncio
from kafka_client import FTEKafkaProducer, TOPICS

app = FastAPI(
    title="Customer Success FTE API",
    description="24/7 AI-powered customer support across Email, WhatsApp, and Web",
    version="2.0.0"
)

# Global producer
producer = FTEKafkaProducer()

@app.on_event("startup")
async def startup_event():
    # Retry mechanism for Kafka (it takes time to boot)
    retries = 5
    while retries > 0:
        try:
            await producer.start()
            print("Kafka Producer started successfully")
            break
        except Exception as e:
            retries -= 1
            print(f"Kafka connection failed ({retries} retries left): {e}")
            await asyncio.sleep(10)
    if retries == 0:
        print("CRITICAL: Failed to connect to Kafka after 5 attempts")

@app.on_event("shutdown")
async def shutdown_event():
    await producer.stop()

# CORS configuration for web support form
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML Frontend for direct experience
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechCorp Support - Digital FTE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">
    <div id="form-container" class="w-full">
        <div class="max-w-2xl mx-auto p-8 bg-white rounded-xl shadow-lg border border-gray-100">
            <div class="mb-8">
                <h2 class="text-3xl font-extrabold text-gray-900 mb-2 text-center md:text-left">Contact TechCorp Support</h2>
                <p class="text-gray-600 text-center md:text-left">
                    Our 24/7 Digital FTE will analyze and resolve your issue immediately.
                </p>
            </div>
            
            <div id="error-message" class="hidden mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg text-red-700">
                <p id="error-text" class="text-sm font-medium"></p>
            </div>
            
            <form id="support-form" class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-2">Name</label>
                        <input type="text" id="name" name="name" required
                            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                            placeholder="John Doe">
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-2">Email</label>
                        <input type="email" id="email" name="email" required
                            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                            placeholder="john@example.com">
                    </div>
                </div>
                
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-2">Subject</label>
                    <input type="text" id="subject" name="subject" required
                        class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                        placeholder="How can we help?">
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-2">Category</label>
                        <select id="category" name="category" 
                            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none">
                            <option value="general">General Question</option>
                            <option value="technical">Technical Support</option>
                            <option value="billing">Billing Inquiry</option>
                            <option value="bug_report">Bug Report</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-2">Urgency</label>
                        <select id="priority" name="priority"
                            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none">
                            <option value="low">Low - Not urgent</option>
                            <option value="medium" selected>Medium - Need help soon</option>
                            <option value="high">High - Urgent issue</option>
                        </select>
                    </div>
                </div>
                
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-2">Detailed Description</label>
                    <textarea id="message" name="message" required rows="5"
                        class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                        placeholder="Please describe your issue..."></textarea>
                </div>
                
                <button type="submit" id="submit-btn"
                    class="w-full py-4 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-700 transition-all transform hover:scale-[1.02] shadow-md">
                    Connect with Support FTE
                </button>
            </form>
        </div>
    </div>

    <script>
        const form = document.getElementById('support-form');
        const submitBtn = document.getElementById('submit-btn');
        const errorDiv = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        const container = document.getElementById('form-container');

        form.onsubmit = async (e) => {
            e.preventDefault();
            errorDiv.classList.add('hidden');
            submitBtn.disabled = true;
            submitBtn.innerText = 'Analyzing Issue...';
            submitBtn.classList.replace('bg-blue-600', 'bg-gray-400');

            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                subject: document.getElementById('subject').value,
                category: document.getElementById('category').value,
                priority: document.getElementById('priority').value,
                message: document.getElementById('message').value
            };

            console.log('Submitting form...', formData);
            try {
                const response = await fetch('/support/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                console.log('Response status:', response.status);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to submit request');
                }
                
                const data = await response.json();
                console.log('Success data:', data);
                
                container.innerHTML = `
                    <div class="max-w-2xl mx-auto p-8 bg-white rounded-xl shadow-lg border border-gray-100">
                        <div class="text-center">
                            <div class="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6">
                                <svg class="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h2 class="text-3xl font-extrabold text-gray-900 mb-2">Success!</h2>
                            <p class="text-lg text-gray-600 mb-6">Your request has been received by our AI Support FTE.</p>
                            <div class="bg-blue-50 rounded-xl p-6 mb-6">
                                <p class="text-sm font-semibold text-blue-600 uppercase tracking-wider mb-1">Your Ticket ID</p>
                                <p class="text-2xl font-mono font-bold text-gray-900">${data.ticket_id}</p>
                            </div>
                            <p class="text-gray-500 mb-8">Check your email shortly for a detailed response from our assistant.</p>
                            <button onclick="window.location.reload()" 
                                class="w-full py-4 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all transform hover:scale-[1.02]">
                                Submit Another Request
                            </button>
                        </div>
                    </div>
                `;
            } catch (err) {
                errorText.innerText = err.message;
                errorDiv.classList.remove('hidden');
                submitBtn.disabled = false;
                submitBtn.innerText = 'Connect with Support FTE';
                submitBtn.classList.replace('bg-gray-400', 'bg-blue-600');
            }
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    return HTML_CONTENT

# Models
class SupportFormSubmission(BaseModel):
    name: str
    email: EmailStr
    subject: str
    category: str
    message: str
    priority: Optional[str] = "medium"

class SupportFormResponse(BaseModel):
    ticket_id: str
    message: str
    estimated_response_time: str

# Endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/support/submit", response_model=SupportFormResponse)
@app.post("/api/support/submit", response_model=SupportFormResponse)
async def submit_support_form(submission: SupportFormSubmission):
    """Handle support form submission."""
    ticket_id = str(uuid.uuid4())
    event = {
        "channel": "web_form",
        "customer_email": submission.email,
        "customer_name": submission.name,
        "subject": submission.subject,
        "content": submission.message,
        "category": submission.category,
        "priority": submission.priority,
        "ticket_id": ticket_id
    }
    await producer.publish(TOPICS['tickets_incoming'], event)
    return SupportFormResponse(
        ticket_id=ticket_id,
        message="Thank you for contacting us! Our AI assistant will respond shortly.",
        estimated_response_time="Usually within 5 minutes"
    )

@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request):
    """Handle simulated Gmail messages."""
    body = await request.json()
    event = {
        "channel": "email",
        "customer_email": body.get("customer_email"),
        "customer_name": body.get("customer_name", "Email User"),
        "subject": body.get("subject", "No Subject"),
        "content": body.get("content", ""),
        "thread_id": body.get("thread_id", str(uuid.uuid4()))
    }
    await producer.publish(TOPICS['tickets_incoming'], event)
    return {"status": "sent to processing", "channel": "email"}

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle simulated WhatsApp messages."""
    body = await request.json()
    event = {
        "channel": "whatsapp",
        "customer_phone": body.get("customer_phone"),
        "customer_name": body.get("customer_name", "WhatsApp User"),
        "content": body.get("content", "")
    }
    await producer.publish(TOPICS['tickets_incoming'], event)
    return {"status": "sent to processing", "channel": "whatsapp"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
