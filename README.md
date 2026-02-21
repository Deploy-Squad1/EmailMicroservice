# EmailMicroservice

Internal email service for the Secret Society platform.

Sends:
- invitation emails
- daily password emails

Built with FastAPI and runs in a separate Docker container.

---

## Endpoints

GET /health  
POST /send-invite  
POST /send-daily-password  

---

## Local development

docker compose up --build

MailHog UI:
http://localhost:8025

Stop containers:

docker compose down
