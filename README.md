# WhatsApp Clinic AI Agent
Flask-based WhatsApp assistant for a clinic, integrating Dialogflow CX for Arabic, custom Hebrew NLP flows, and an admin dashboard for managing patients and follow-ups.
## Features
- WhatsApp Cloud API webhook for inbound/outbound messaging.
- Dialogflow CX integration for Arabic conversations.
- Custom Hebrew NLP flow manager and templated responses.
- Admin dashboard (Flask-Admin) for patients, follow-ups, and message history.
- Scheduler for automated follow-ups and background tasks.
## Tech Stack
- Python 3.9, Flask, Gunicorn
- MongoDB (pymongo)
- Google Cloud Dialogflow CX
- WhatsApp Cloud API
- APScheduler
## Project Structure
- `app.py`: main Flask app, webhook endpoints, message processing.
- `custom_nlp/`: Hebrew NLP flow logic and response generation.
- `dashboard/`: Admin UI models and views.
- `utils/`: WhatsApp, Dialogflow, language utilities, and storage helpers.
- `tasks.py`: background task routes.
- `Test/`: test scripts and verification helpers.
## Setup
1) Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) Create a `.env` file with the required variables:
- `FLASK_SECRET_KEY`
- `MONGODB_URI`
- `MONGODB_DB_NAME`
- `GOOGLE_CLOUD_PROJECT`
- `DIALOGFLOW_LOCATION`
- `DIALOGFLOW_AGENT_ID`
- `WHATSAPP_API_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_WEBHOOK_TOKEN`
3) Place your Google Cloud service account key at `service_account.json`.
## Run Locally
```bash
python app.py
```
The app listens on `http://localhost:5000` by default.
## Webhook Endpoints
- `GET /webhook`: WhatsApp verification.
- `POST /webhook`: Incoming WhatsApp messages.
## Admin Dashboard
Visit `/dashboard` and log in with a valid user from the database.
## Deployment
The project includes `app.yaml` and `cron.yaml` for Google App Engine.
Typical deploy command:
```bash
gcloud app deploy
```
## Tests
Test scripts are under `Test/`.
Example:
```bash
python Test/test_webhook.py
```
## Security Notes
- Do not commit `.env` or `service_account.json`.
- Store real secrets in environment variables or a secret manager.
## License
Proprietary. All rights reserved
