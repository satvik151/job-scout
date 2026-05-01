import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path('backend/.env'), override=True)

sender = os.getenv('SENDER_EMAIL')
api_key = os.getenv('RESEND_API_KEY')

print(f'Sender: {sender}')
print(f'API Key exists: {bool(api_key)}')

resp = requests.post(
    'https://api.resend.com/emails',
    headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    },
    json={
        'from': sender,
        'to': 'satvikislegendary@gmail.com',
        'subject': 'Job Scout Digest',
        'text': 'This is your job digest.'
    },
    timeout=15
)
print(f'Status: {resp.status_code}')
print(f'Response: {resp.text}')
