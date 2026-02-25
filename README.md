# EmailMicroservice

Internal email service for the Secret Society platform.

Sends:
- invitation emails
- daily password emails

Built with FastAPI and runs as a dedicated Docker container.

## Role

The EmailMicroservice:
- receives email requests from the Core service
- sends emails via SMTP
- returns delivery status to Core
- in Dev-mode, emails are captured by MalilHog

---

## Endpoints

GET /health  
POST /send-invite  
POST /send-daily-password 

---
## Environment Variables

Required:
- SMTP_HOST

Optional:
- SMTP_PORT (default: 25)
- SMTP_USER
- SMTP_PASS
- FROM_EMAIL (default: noreply@local)

---
## Error Handling

SMTP/network errors return 502 Email delivery failed
Configuration errors (e.g. SMTP_HOST) cause the conteiner to exit.
Internal SMTP errors are logged but not exposed to clients.

---
## Logging

Logs are written to stdout. 
No email content or credentials are logged.

---
## Local testing

Start services:
docker compose up --build

Healthcheck:
curl http://localhost:8081/health

Send Invite:
curl -X POST http://localhost:8081/send-invite \
  -H "Content-Type: application/json" \
  -d '{"to_email":"user@secret-society.local","invite_link":"https://example.com"}'

Check email in MailHog UI:
http://localhost:8025

Stop containers:

docker compose down
