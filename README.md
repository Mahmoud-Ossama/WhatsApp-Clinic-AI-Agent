# WhatsApp-Dialogflow CX Integration

This webhook handles communication between WhatsApp (via Twilio) and Dialogflow CX.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- GOOGLE_CLOUD_PROJECT
- DIALOGFLOW_LOCATION
- DIALOGFLOW_AGENT_ID

3. Set up Google Cloud Authentication:
   - Go to Google Cloud Console
   - Navigate to IAM & Admin > Service Accounts
   - Create a new service account or select existing one
   - Create a new key (JSON format)
   - Download and save as `service-account.json` in the project root directory

4. Run the application:
```bash
python app.py
```

5. Configure Twilio WhatsApp webhook URL to point to your `/webhook` endpoint.

## Local Testing Setup

1. Install ngrok:
```bash
# Windows (using chocolatey)
choco install ngrok

# Or download from https://ngrok.com/download
```

2. Run ngrok to create a tunnel:
```bash
ngrok http 5000
```

3. Copy the HTTPS URL (e.g., https://your-ngrok-url.ngrok.io)

4. Configure Twilio Webhook:
   - Go to Twilio Console
   - Find your WhatsApp Sandbox
   - Set the webhook URL to: https://your-ngrok-url.ngrok.io/webhook

5. Test endpoints:
   - Root: https://your-ngrok-url.ngrok.io/
   - Webhook: https://your-ngrok-url.ngrok.io/webhook

## Troubleshooting

### Authentication Issues
- Ensure `service-account.json` is in the project root directory
- Verify the service account has the necessary permissions:
  - Dialogflow API Admin
  - Dialogflow Client API
- Check that the project ID in service account matches GOOGLE_CLOUD_PROJECT in .env

### Webhook Not Found
- Ensure the Flask server is running
- Verify the ngrok tunnel is active
- Check the full URL path is correct
- Try accessing the root path (/) first
- Check server logs for request details

## Usage

The webhook will automatically:
1. Receive messages from WhatsApp
2. Forward them to Dialogflow CX
3. Send responses back to the user via WhatsApp
