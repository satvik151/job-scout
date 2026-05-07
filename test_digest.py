import requests
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas

BASE_URL = "http://localhost:8000"
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

print("=" * 70)
print("TESTING EMAIL DIGEST ENDPOINT")
print("=" * 70)

# Create a test user
print("\n[1] Creating test user...")
email = f"digest.test.{timestamp}@example.com"
r = requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": "TestPass123"})
if r.status_code == 200:
    user_id = r.json()["id"]
    print(f"✓ User created (ID: {user_id}, Email: {email})")
else:
    print(f"✗ Failed: {r.status_code} - {r.text}")
    exit(1)

# Login
print("\n[2] Logging in...")
r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": "TestPass123"})
if r.status_code == 200:
    token = r.json()["access_token"]
    print(f"✓ Logged in, token: {token[:40]}...")
else:
    print(f"✗ Failed: {r.status_code} - {r.text}")
    exit(1)

# Upload resume
print("\n[3] Uploading resume...")
buffer = BytesIO()
c = canvas.Canvas(buffer)
c.drawString(100, 750, "Test resume for digest verification with enough content")
c.drawString(100, 730, "Senior Python Developer with FastAPI experience")
c.save()
buffer.seek(0)

r = requests.post(
    f"{BASE_URL}/auth/upload-resume",
    headers={"Authorization": f"Bearer {token}"},
    files={"file": ("resume.pdf", buffer.getvalue(), "application/pdf")}
)
if r.status_code == 200:
    print(f"✓ Resume uploaded")
else:
    print(f"✗ Failed: {r.status_code} - {r.text}")
    exit(1)

# Send digest
print("\n[4] Sending email digest...")
r = requests.post(
    f"{BASE_URL}/send-digest",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Status Code: {r.status_code}")
result = r.json()
print(f"Response: {result}")

if r.status_code == 200:
    print("\n✓✓✓ EMAIL DIGEST SENT SUCCESSFULLY ✓✓✓")
    print(f"  Recipient: {result.get('recipient', 'N/A')}")
    print(f"  Jobs in digest: {result.get('jobs_in_digest', 0)}")
else:
    print(f"\n✗ Failed to send digest: {r.text}")

print("\n" + "=" * 70)
