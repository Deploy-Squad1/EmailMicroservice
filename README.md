# EmailMicroservice

Internal email service for the Secret Society platform.

Sends:

- invitation emails
- daily password emails

Built with FastAPI and runs as a dedicated Docker container.

## Role

The EmailMicroservice delivers emails requested by other services.

It:

- receives invitation requests from the FrontendMicroservice
- receives daily password notifications from the CoreMicroservice
- validates JWT authentication and user role
- sends emails via SMTP
- returns delivery status to the caller

Only users with the role **Gold** are allowed to send invitation emails.

Emails are captured by MailHog in development mode.

## Endpoints

GET `/health` - health check endpoint\
POST `/send-invite` - sends an invitation email\
POST `/send-daily-password` - sends a daily password email

## Configuration

The service reads environment variables from .env used by docker-compose.yml.

Currently required:

`DJANGO_SECRET_KEY` - used to verify JWT tokens issued by the Core service.

## Error Handling

- SMTP/network errors return 502 Email delivery failed
- Missing configurations (e.g. SMTP_HOST) stops the container on startup.
- Internal SMTP errors are logged but not exposed to clients.

## Logging

Logs are written to stdout.\
No email content or credentials are logged.

## Local testing

Start the service:

```bash
docker compose up --build
```

Healthcheck:

```bash
curl <http://localhost:8081/health>
```

Send Invite:

```bash
curl -X POST http://localhost:8081/send-invite \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=<TOKEN>" \
  -d '{"to_email":"user@example.com","invite_link":"https://example.com"}'
```

Check email in MailHog UI:\
<http://localhost:8025>
