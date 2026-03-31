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

## 🛠 Tech Stack

- **Language**: Python 3.11
- **API Framework**: FastAPI (Uvicorn)
- **Agent Framework**: OpenAI Agents SDK (`openai-agents`)
- **AI Engine**: Google Gemini API
- **Message Broker**: Apache Kafka & Zookeeper (Bitnami images)
- **Database**: PostgreSQL with `pgvector`
- **Containerization**: Docker & Docker Compose
- **Channels**:
  - **WhatsApp**: Twilio API
  - **Email**: Gmail API (OAuth2)

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
   git clone <repo-url>
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

## 🛠 Commands Reference

| Task | Command |
| :--- | :--- |
| Start all services | `docker-compose up --build` |
| Stop all services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Restart a specific service | `docker-compose restart worker` |

---

## ⚠️ Troubleshooting

- **Docker Image Errors**: If you get a "Not Found" error for Bitnami images, ensure you are using the `bitnamilegacy` repository in `docker-compose.yml` for specific older versions.
- **Kafka Connection**: If the worker fails to connect, wait a few seconds for Kafka to fully initialize before restarting the worker.
- **Port Conflicts**: Ensure ports `5432`, `9092`, `2181`, and `8000` are free on your host machine.
