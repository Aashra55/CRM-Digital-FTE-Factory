# CRM Digital FTE - AI Customer Success Agent

This project is an **AI-driven Customer Success Full-Time Equivalent (FTE)** designed to handle customer inquiries across multiple channels (Gmail, WhatsApp, and Web Forms) autonomously. It uses Google's Gemini Pro for intelligent response generation and Kafka for scalable message processing.

---

## 🚀 Features

- **Omnichannel Support**: Handles incoming messages from Gmail, WhatsApp (via Twilio), and a Custom Web Form.
- **AI-Powered Responses**: Uses Gemini 1.5 Pro/Flash to provide context-aware, human-like answers based on internal product documentation.
- **Smart Escalation**: Automatically identifies complex issues (e.g., refunds, technical bugs) and flags them for human intervention.
- **Knowledge Base Integration**: Utilizes a `context/` directory containing product docs, brand voice, and escalation rules to ground AI responses.
- **Asynchronous Processing**: Uses Kafka to decouple message reception from processing, ensuring high availability and reliability.
- **Vector Search Ready**: Includes PostgreSQL with `pgvector` for future implementation of RAG (Retrieval-Augmented Generation).

---

## 🛠 Tech Stack & Use Cases

Here is a breakdown of the technologies used and why they were chosen for this project:

### 1. **Python 3.11** (The Core Language)
- **Role**: The primary programming language for the entire backend.
- **Why**: It is the industry standard for AI and data processing, offering excellent libraries for interacting with Gemini and Kafka.

### 2. **FastAPI (Uvicorn)** (The Receptionist/API Gateway)
- **Role**: Handles incoming webhooks from Web Forms, Gmail, and WhatsApp.
- **Why**: It is extremely fast and automatically generates documentation. It acts as the entry point for all customer messages.

### 3. **Google Gemini API** (The AI Brain)
- **Role**: Understands user queries, generates human-like responses, and decides when to create tickets or escalate issues.
- **Why**: It offers high-quality reasoning and handles long context (like product docs) better than most other AI models.

### 4. **Apache Kafka & Zookeeper** (The Postman/Message Broker)
- **Role**: Manages the flow of messages between the API and the AI Worker.
- **Why**: It ensures that no message is lost even if the system is busy. It allows the system to handle hundreds of messages simultaneously by queuing them.

### 5. **PostgreSQL with pgvector** (The Memory/Database)
- **Role**: Stores customer profiles, conversation history, and support tickets.
- **Why**: `pgvector` allows the AI to perform "Semantic Search," meaning it can find the most relevant answer in the Knowledge Base based on the *meaning* of the question, not just keywords.

### 6. **Docker & Docker Compose** (The Portable Box)
- **Role**: Packages the entire project (DB, Kafka, AI, API) into containers.
- **Why**: It ensures the project runs exactly the same way on any computer (Windows, Mac, or Linux) without needing to install each tool manually.

### 7. **OpenAI Agents SDK** (The Orchestrator)
- **Role**: Manages how the AI uses "Tools" (like creating tickets or searching docs).
- **Why**: It provides a structured way for the AI to "think" before it speaks, making sure it follows the required workflow (Ticket -> History -> Knowledge Base -> Response).

### 8. **Gmail API, Twilio & Custom Web Form** (The Communication Channels)
- **Role**: Connects the AI to the real world through Email, WhatsApp, and your Website.
- **Why**: 
    - **Gmail**: For formal support via email.
    - **Twilio**: For instant support via WhatsApp.
    - **Web Form**: A direct way for users to submit issues from your website.

---

## 📂 Project Structure

```text
CRM_Digital_FTE/
├── production/             # Core application code
│   ├── agent/              # AI logic and tool definitions
│   ├── api/                # FastAPI endpoints for webhooks
│   ├── channels/           # Gmail and WhatsApp handlers
│   ├── database/           # SQL schemas and queries
│   ├── workers/            # Kafka message processors
│   └── Dockerfile          # Container build instructions
├── context/                # Grounding data for AI
│   ├── product-docs.md     # Product information
│   ├── brand-voice.md      # Style guidelines
│   └── escalation-rules.md # When to hand over to a human
├── specs/                  # Technical specifications and logs
├── docker-compose.yml      # Orchestration for DB, Kafka, and App
└── .env                    # Environment variables (Secrets)
```

---

## 🔑 Credentials & Environment Variables

Create a `.env` file in the root. Here is the full list of required variables:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini Pro API Key | `AIzaSy...` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | `your_token` |
| `TWILIO_WHATSAPP_NUMBER` | Twilio Sandbox Number | `whatsapp:+12345678910` |
| `DATABASE_URL` | Postgres Connection String | `postgresql://postgres:postgres@db:5432/fte_db` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka Broker Address | `kafka:9092` |

---

## 📊 Kafka Topics

The system uses three main topics for asynchronous communication:
- `incoming_messages`: Raw messages from all channels (Gmail, WhatsApp, Web).
- `processed_messages`: Messages analyzed by AI, ready for response.
- `outgoing_messages`: Messages to be sent back to the customer.

---

## 🗄️ Database Schema

The `fte_db` database consists of:
- **`customers`**: Stores unique customer IDs, names, and channel info.
- **`conversations`**: Tracks sessions between customers and the AI.
- **`messages`**: Logs every single message, its timestamp, and whether it was escalated.

---

## 🧪 Testing

To ensure everything is working correctly, run the built-in tests:

### Running tests with Docker:
```bash
docker-compose run api pytest
```

### Running a specific test:
```bash
docker-compose run api pytest tests/test_gemini_agent.py
```

---

## 🛠 Manual Development (Non-Docker)

If you want to run the application locally (without Docker) for faster debugging:

1. **Install dependencies**:
   ```bash
   cd production
   pip install -r requirements.txt
   ```
2. **Start the API**:
   ```bash
   uvicorn api.main:app --reload
   ```
3. **Start the Message Processor**:
   ```bash
   python workers/message_processor.py
   ```
   *Note: You still need a running Kafka and Postgres instance (you can run just those using Docker).*

---

## ⚙️ Installation & Running

### Prerequisites
- Docker & Docker Compose installed.

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Aashra55/CRM-Digital-FTE-Factory
   cd CRM_Digital_FTE
   ```

2. **Configure Environment**:
   Create a `.env` file in the root directory (refer to `.env.example` if available):
   ```env
   GEMINI_API_KEY=your_key_here
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+12345678910
   ```

3. **Start the Project**:
   Run the following command to build and start all services (DB, Kafka, API, Worker):
   ```powershell
   docker-compose up --build
   ```

---

## 🔄 Workflow

1. **Incoming Message**: A user sends an email or WhatsApp message.
2. **Webhook**: The `api` service receives the message and pushes it into a Kafka topic (`incoming_messages`).
3. **Processing**: The `worker` service (Message Processor) consumes the message from Kafka.
4. **AI Generation**: 
   - The worker fetches product context from `context/`.
   - It sends the user query + context to **Gemini**.
   - Gemini decides if the message needs escalation or a direct response.
5. **Outgoing Response**: The response is sent back via the respective channel (Gmail/Twilio).
6. **Storage**: The conversation is stored in the PostgreSQL database for history.

---

## 🚀 Commands Reference

Use these commands depending on which part of the system you want to run.

### 1. Full System (Recommended)
Starts everything: Database, Kafka, API (Web Form), and Worker (Gmail/WhatsApp).
```bash
docker-compose up --build
```

### 2. Web Form Only (User Queries)
If you only want to use the Web Form to send queries and receive AI replies via email.
```bash
docker-compose up api
```
*Access the form at: `http://localhost:8000`*

### 3. Gmail Inbox Processing (Auto-Reply)
If you want the AI to read an authorized Gmail inbox and reply to new emails automatically.
```bash
docker-compose up worker
```

### 4. Stopping the System
```bash
docker-compose down
```

### 5. Restart & Reset (After changing API Keys or Models)
Use this to stop all services and restart the worker with a fresh state.
```bash
docker-compose down && docker-compose up worker
```

---

## 🛠 Quick Commands Reference

| Task | Command |
| :--- | :--- |
| Start all services | `docker-compose up --build` |
| Stop all services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Restart a specific service | `docker-compose restart worker` |

---

## 📧 Gmail Authorization Guide

To let the AI read your emails, you must authorize it once. Follow these steps:

1. **Start the Worker**: Run `docker-compose up worker`.
2. **Find the Link**: Look at the terminal logs for a message saying `GMAIL AUTHENTICATION REQUIRED`.
3. **Authorize**: Copy the long URL (starting with `https://accounts.google.com...`), paste it into your browser, and click "Allow".
4. **Get the Code**: You will land on a page that fails to load (localhost:8080). Look at the URL bar and copy the text after `code=`.
5. **Save the Code**: Create a file named `production/auth_code.txt` and paste that code inside it.
6. **Done**: The worker will detect the file, create `token.json`, and start processing your inbox.

---

## 🛠 Manual Development (Non-Docker)

If you want to run services directly on your machine:

1. **Install dependencies**:
   ```bash
   cd production
   pip install -r requirements.txt
   ```
2. **Start the API**:
   ```bash
   uvicorn api.main:app --reload
   ```
3. **Start the Worker**:
   ```bash
   python workers/message_processor.py
   ```
   *(Note: You still need Kafka and Postgres running in the background via Docker).*

---

## 🧪 Testing

To verify the AI agent logic without sending real emails:
```bash
docker-compose run api pytest production/test_gemini_agent.py
```

---

## ⚠️ Troubleshooting

- **Docker Image Errors**: If you get a "Not Found" error for Bitnami images, ensure you are using the `bitnamilegacy` repository in `docker-compose.yml` for specific older versions.
- **Kafka Connection**: If the worker fails to connect, wait a few seconds for Kafka to fully initialize before restarting the worker.
- **Port Conflicts**: Ensure ports `5432`, `9092`, `2181`, and `8000` are free on your host machine.

---

## 🔑 Key Configuration
- **Gemini Model**: Configured in `production/agent/customer_success_agent.py`.
- **Environment**: Set your `GEMINI_API_KEY` in the root `.env` file.
- **Database**: Postgres runs on port `5432`.
- **API**: FastAPI runs on port `8000`.
