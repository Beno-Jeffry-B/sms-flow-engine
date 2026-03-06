# Surge AI SMS Playground

A developer tool that allows you to test the Surge SMS API from a web interface, inspect webhook logs, and optionally enable AI-powered automatic SMS replies.

## Tech Stack
- Frontend: Next.js (React), TypeScript, TailwindCSS
- Backend: FastAPI (Python)
- Database: PostgreSQL
- AI: Groq API (LLM)
- Deployment: Docker Compose

## Setup Instructions

1. **Clone the repository.**
2. **Copy `.env.example` to `.env`** and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   *Required variables: `SURGE_API_KEY`, `GROQ_API_KEY` (for AI replies).*
3. **Start the application using Docker Compose:**
   ```bash
   docker-compose up --build
   ```
4. **Access the application:**
   - Frontend: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
   - Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Webhook Endpoint: `http://localhost:8000/webhook/surge`

## Features
- **Send SMS**: Input a phone number and message text, taking advantage of the Surge API.
- **Webhook Receiver**: Exposes an endpoint to receive incoming Surge webhooks, displaying payloads in real-time on the dashboard.
- **SMS Logs**: Visualize sent, received, and AI-auto-replied messages.
- **AI Auto Reply**: Optionally enable Groq-powered intent classification and reply generation for incoming messages.
